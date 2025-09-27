"""
AI-powered weakness detection and coaching insights service for RocketTrainer.
"""
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import structlog

from app.schemas.coaching import (
    CoachingInsights, PerformanceArea, WeaknessInsight, StrengthInsight,
    PerformanceMetrics, AnalysisContext
)
from app.schemas.replay import PlayerStats
from app.services.natural_language_service import NaturalLanguageService

logger = structlog.get_logger()


class WeaknessDetectionService:
    """Service for analyzing player performance and generating coaching insights."""
    
    # Performance area definitions with metric weights
    PERFORMANCE_AREAS = {
        'positioning': {
            'primary_metrics': ['positioning_score'],
            'supporting_metrics': ['time_on_ground', 'defensive_actions_per_minute'],
            'weights': [0.7, 0.2, 0.1],
            'description': 'Field positioning and spatial awareness'
        },
        'rotation': {
            'primary_metrics': ['rotation_score'],
            'supporting_metrics': ['defensive_actions_per_minute', 'offensive_actions_per_minute'],
            'weights': [0.8, 0.1, 0.1],
            'description': 'Team rotation and positioning flow'
        },
        'mechanics': {
            'primary_metrics': ['aerial_efficiency'],
            'supporting_metrics': ['average_speed', 'time_supersonic'],
            'weights': [0.6, 0.2, 0.2],
            'description': 'Car control and mechanical skill'
        },
        'game_sense': {
            'primary_metrics': ['assists_per_minute', 'saves_per_minute'],
            'supporting_metrics': ['goals_per_minute', 'shots_per_minute'],
            'weights': [0.3, 0.3, 0.2, 0.2],
            'description': 'Decision making and game awareness'
        },
        'boost_management': {
            'primary_metrics': ['boost_efficiency'],
            'supporting_metrics': ['boost_usage'],
            'weights': [0.7, 0.3],
            'description': 'Boost collection and usage efficiency'
        }
    }
    
    def __init__(self):
        """Initialize the weakness detection service."""
        self.logger = logger.bind(service="weakness_detection")
        self.nlp_service = NaturalLanguageService()
    
    def analyze_performance(
        self, 
        player_stats: PlayerStats, 
        context: AnalysisContext
    ) -> CoachingInsights:
        """
        Analyze player performance and generate comprehensive coaching insights.
        
        Args:
            player_stats: Raw player statistics from replay
            context: Match context information
            
        Returns:
            CoachingInsights with detailed analysis and recommendations
        """
        start_time = datetime.utcnow()
        
        try:
            # Normalize metrics for analysis
            normalized_metrics = self._normalize_metrics(player_stats, context)
            
            # Calculate composite scores for each performance area
            performance_areas = self._calculate_composite_scores(normalized_metrics)
            
            # Detect weaknesses and strengths
            weaknesses = self._detect_weaknesses(performance_areas, context)
            strengths = self._detect_strengths(performance_areas, context)
            
            # Calculate overall performance score
            overall_score = self._calculate_overall_score(performance_areas)
            
            # Determine improvement priority
            improvement_priority = self._determine_improvement_priority(weaknesses)
            
            # Generate key takeaway message
            key_takeaway = self._generate_key_takeaway(weaknesses, strengths, context)
            
            insights = CoachingInsights(
                match_id=context.match_id if hasattr(context, 'match_id') else "unknown",
                overall_performance_score=overall_score,
                performance_areas=performance_areas,
                top_weaknesses=weaknesses[:3],  # Top 3 weaknesses
                top_strengths=strengths[:2],    # Top 2 strengths
                improvement_priority=improvement_priority,
                key_takeaway=key_takeaway,
                generated_at=datetime.utcnow(),
                confidence_score=self._calculate_confidence_score(normalized_metrics)
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.logger.info(
                "Generated coaching insights",
                match_id=getattr(context, 'match_id', 'unknown'),
                processing_time_ms=processing_time,
                weaknesses_count=len(weaknesses),
                strengths_count=len(strengths)
            )
            
            return insights
            
        except Exception as e:
            self.logger.error(
                "Failed to generate coaching insights",
                error=str(e),
                match_id=getattr(context, 'match_id', 'unknown')
            )
            raise
    
    def _normalize_metrics(self, player_stats: PlayerStats, context: AnalysisContext) -> PerformanceMetrics:
        """Normalize raw player statistics for consistent analysis."""
        duration_minutes = context.duration / 60.0 if context.duration > 0 else 1.0
        
        return PerformanceMetrics(
            # Normalize counting stats by match duration and scale to 0-1
            goals_per_minute=self._normalize_per_minute_stat((player_stats.goals or 0) / duration_minutes, max_value=2.0),
            assists_per_minute=self._normalize_per_minute_stat((player_stats.assists or 0) / duration_minutes, max_value=3.0),
            saves_per_minute=self._normalize_per_minute_stat((player_stats.saves or 0) / duration_minutes, max_value=5.0),
            shots_per_minute=self._normalize_per_minute_stat((player_stats.shots or 0) / duration_minutes, max_value=8.0),
            score_per_minute=self._normalize_per_minute_stat((player_stats.score or 0) / duration_minutes, max_value=1000.0),
            
            # Direct metrics (already normalized 0-1)
            positioning_score=player_stats.positioning_score,
            rotation_score=player_stats.rotation_score,
            boost_efficiency=player_stats.boost_efficiency,
            aerial_efficiency=player_stats.aerial_efficiency,
            
            # Time distribution metrics (already normalized 0-1)
            time_supersonic=player_stats.time_supersonic,
            time_on_ground=player_stats.time_on_ground,
            time_low_air=player_stats.time_low_air,
            time_high_air=player_stats.time_high_air,
            
            # Action counts normalized by duration and scaled to 0-1
            defensive_actions_per_minute=self._normalize_per_minute_stat((player_stats.defensive_actions or 0) / duration_minutes, max_value=20.0),
            offensive_actions_per_minute=self._normalize_per_minute_stat((player_stats.offensive_actions or 0) / duration_minutes, max_value=30.0),
            
            # Speed metrics (normalize to 0-1 scale)
            average_speed=self._normalize_speed(player_stats.average_speed),
            boost_usage=player_stats.boost_usage
        )
    
    def _normalize_speed(self, speed: Optional[float]) -> Optional[float]:
        """Normalize speed to 0-1 scale (0 = 0 uu/s, 1 = 2300 uu/s max speed)."""
        if speed is None:
            return None
        return min(speed / 2300.0, 1.0)

    def _normalize_per_minute_stat(self, value: float, max_value: float) -> float:
        """Normalize a per-minute statistic to 0-1 scale."""
        return min(value / max_value, 1.0)
    
    def _calculate_composite_scores(self, metrics: PerformanceMetrics) -> List[PerformanceArea]:
        """Calculate composite scores for each performance area."""
        performance_areas = []
        
        for area_name, config in self.PERFORMANCE_AREAS.items():
            all_metrics = config['primary_metrics'] + config['supporting_metrics']
            weights = config['weights']
            
            weighted_score = 0.0
            total_weight = 0.0
            contributing_metrics = []
            
            for i, metric_name in enumerate(all_metrics):
                metric_value = getattr(metrics, metric_name, None)
                if metric_value is not None:
                    weight = weights[i] if i < len(weights) else 0.1
                    weighted_score += metric_value * weight
                    total_weight += weight
                    contributing_metrics.append(metric_name)
            
            # Calculate final score and ensure it's within 0-1 range
            if total_weight > 0:
                final_score = min(weighted_score / total_weight, 1.0)
            else:
                final_score = 0.5  # Default to average if no data
            
            # Determine status
            if final_score >= 0.7:
                status = 'strength'
            elif final_score >= 0.4:
                status = 'average'
            else:
                status = 'weakness'
            
            performance_area = PerformanceArea(
                name=area_name,
                score=final_score,
                status=status,
                contributing_metrics=contributing_metrics,
                raw_score=weighted_score
            )
            
            performance_areas.append(performance_area)
        
        return performance_areas
    
    def _detect_weaknesses(
        self, 
        performance_areas: List[PerformanceArea], 
        context: AnalysisContext
    ) -> List[WeaknessInsight]:
        """Detect and analyze performance weaknesses."""
        weaknesses = []
        
        # Sort areas by score (lowest first) and filter for actual weaknesses
        weak_areas = [area for area in performance_areas if area.score < 0.6]
        weak_areas.sort(key=lambda x: x.score)
        
        for area in weak_areas[:3]:  # Top 3 weaknesses
            severity = 1.0 - area.score  # Higher score = lower severity
            impact_potential = self._calculate_impact_potential(area, context)
            
            weakness = WeaknessInsight(
                area=area.name,
                severity=severity,
                impact_potential=impact_potential,
                primary_issue=self._identify_primary_issue(area),
                coaching_feedback=self._generate_coaching_feedback(area, context),
                specific_recommendations=self._get_recommendations(area.name),
                confidence=self._calculate_area_confidence(area)
            )
            
            weaknesses.append(weakness)
        
        # Sort by priority (severity * impact_potential)
        weaknesses.sort(key=lambda w: w.severity * w.impact_potential, reverse=True)
        
        return weaknesses
    
    def _detect_strengths(
        self, 
        performance_areas: List[PerformanceArea], 
        context: AnalysisContext
    ) -> List[StrengthInsight]:
        """Detect and highlight performance strengths."""
        strengths = []
        
        # Filter for actual strengths
        strong_areas = [area for area in performance_areas if area.score >= 0.7]
        strong_areas.sort(key=lambda x: x.score, reverse=True)
        
        for area in strong_areas[:2]:  # Top 2 strengths
            strength = StrengthInsight(
                area=area.name,
                score=area.score,
                positive_feedback=self._generate_positive_feedback(area),
                leverage_suggestions=self._get_leverage_suggestions(area.name)
            )
            strengths.append(strength)
        
        return strengths

    def _calculate_impact_potential(self, area: PerformanceArea, context: AnalysisContext) -> float:
        """Calculate the potential impact of improving this area."""
        base_impact = 1.0 - area.score  # Lower score = higher improvement potential

        # Adjust based on area importance for different playlists
        if context.playlist.lower() in ['ranked_standard', 'ranked_doubles']:
            if area.name in ['positioning', 'rotation']:
                base_impact *= 1.2  # These are more important in ranked

        # Adjust based on match result
        if context.result == 'loss' and area.name in ['positioning', 'game_sense']:
            base_impact *= 1.1  # These might have contributed to the loss

        return min(base_impact, 1.0)

    def _identify_primary_issue(self, area: PerformanceArea) -> str:
        """Identify the primary issue in a performance area."""
        issue_templates = {
            'positioning': "Poor field positioning and spatial awareness",
            'rotation': "Inconsistent team rotation and positioning flow",
            'mechanics': "Limited car control and mechanical execution",
            'game_sense': "Suboptimal decision making and game awareness",
            'boost_management': "Inefficient boost collection and usage"
        }

        return issue_templates.get(area.name, f"Performance issues in {area.name}")

    def _calculate_overall_score(self, performance_areas: List[PerformanceArea]) -> float:
        """Calculate overall performance score across all areas."""
        if not performance_areas:
            return 0.5

        # Weight different areas by importance
        area_weights = {
            'positioning': 0.25,
            'rotation': 0.25,
            'game_sense': 0.20,
            'mechanics': 0.15,
            'boost_management': 0.15
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for area in performance_areas:
            weight = area_weights.get(area.name, 0.1)
            weighted_sum += area.score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.5

    def _determine_improvement_priority(self, weaknesses: List[WeaknessInsight]) -> str:
        """Determine the primary area to focus improvement efforts."""
        if not weaknesses:
            return "Continue developing all areas consistently"

        primary_weakness = weaknesses[0]  # Already sorted by priority

        priority_messages = {
            'positioning': "Focus on field positioning and spatial awareness",
            'rotation': "Prioritize team rotation and positioning flow",
            'mechanics': "Work on car control and mechanical skills",
            'game_sense': "Develop decision making and game awareness",
            'boost_management': "Improve boost collection and usage efficiency"
        }

        return priority_messages.get(primary_weakness.area, f"Focus on improving {primary_weakness.area}")

    def _calculate_confidence_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate confidence in the analysis based on available data."""
        total_metrics = 0
        available_metrics = 0

        for field_name, field_value in metrics.__dict__.items():
            if not field_name.startswith('_'):
                total_metrics += 1
                if field_value is not None:
                    available_metrics += 1

        data_completeness = available_metrics / total_metrics if total_metrics > 0 else 0

        # Base confidence starts at 0.6, increases with data completeness
        confidence = 0.6 + (data_completeness * 0.4)

        return min(confidence, 1.0)

    def _calculate_area_confidence(self, area: PerformanceArea) -> float:
        """Calculate confidence for a specific performance area."""
        # More contributing metrics = higher confidence
        metric_count = len(area.contributing_metrics)

        if metric_count >= 3:
            return 0.9
        elif metric_count == 2:
            return 0.8
        elif metric_count == 1:
            return 0.7
        else:
            return 0.5

    def _generate_coaching_feedback(self, area: PerformanceArea, context: AnalysisContext) -> str:
        """Generate coaching feedback for a performance area."""
        return self.nlp_service.generate_coaching_feedback(area, context)

    def _generate_positive_feedback(self, area: PerformanceArea) -> str:
        """Generate positive feedback for a strength area."""
        return self.nlp_service.generate_positive_feedback(area)

    def _get_recommendations(self, area_name: str) -> List[str]:
        """Get specific recommendations for improving a performance area."""
        return self.nlp_service.get_recommendations(area_name)

    def _get_leverage_suggestions(self, area_name: str) -> List[str]:
        """Get suggestions for leveraging a strength area."""
        return self.nlp_service.get_leverage_suggestions(area_name)

    def _generate_key_takeaway(
        self,
        weaknesses: List[WeaknessInsight],
        strengths: List[StrengthInsight],
        context: AnalysisContext
    ) -> str:
        """Generate a key takeaway message for the overall analysis."""
        primary_weakness = weaknesses[0].area if weaknesses else None
        primary_strength = strengths[0].area if strengths else None

        return self.nlp_service.generate_key_takeaway(primary_weakness, primary_strength, context)
