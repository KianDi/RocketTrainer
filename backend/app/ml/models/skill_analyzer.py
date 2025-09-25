"""
Skill Analyzer for RocketTrainer

Provides detailed skill analysis and performance metrics across
different gameplay categories using statistical analysis and ML.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import structlog

from ..config import ml_config, SkillCategory
from ..features.pipeline import FeatureEngineeringPipeline
from ..features.preprocessor import create_skill_category_features
from ...models.match import Match

logger = structlog.get_logger(__name__)


class SkillAnalyzer:
    """Analyzes player skills across different gameplay categories."""
    
    def __init__(self, 
                 percentile_calculation: str = "rank_based",
                 trend_window: int = 5):
        """
        Initialize skill analyzer.
        
        Args:
            percentile_calculation: Method for percentile calculation ('rank_based', 'population')
            trend_window: Number of recent matches for trend analysis
        """
        self.percentile_calculation = percentile_calculation
        self.trend_window = trend_window
        
        # Feature pipeline for consistent feature extraction
        self.feature_pipeline = FeatureEngineeringPipeline(
            use_feature_selection=False,  # Keep all features for detailed analysis
            scaler_type="standard"
        )
        
        # Skill category definitions
        self.skill_categories = {cat.value: cat for cat in ml_config.skill_categories}
        
        # Performance benchmarks (will be updated with population data)
        self.performance_benchmarks = self._initialize_benchmarks()
        
        logger.info("SkillAnalyzer initialized",
                   percentile_calculation=percentile_calculation,
                   trend_window=trend_window,
                   skill_categories=len(self.skill_categories))
    
    def _initialize_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """Initialize performance benchmarks for skill categories."""
        # These are initial benchmarks - in production, these would be
        # calculated from population data
        return {
            "mechanical": {
                "shot_accuracy": {"bronze": 0.2, "silver": 0.3, "gold": 0.4, "platinum": 0.5, "diamond": 0.6},
                "save_percentage": {"bronze": 0.3, "silver": 0.4, "gold": 0.5, "platinum": 0.6, "diamond": 0.7},
                "goals_per_minute": {"bronze": 0.3, "silver": 0.4, "gold": 0.5, "platinum": 0.6, "diamond": 0.7}
            },
            "positioning": {
                "average_speed": {"bronze": 800, "silver": 900, "gold": 1000, "platinum": 1100, "diamond": 1200},
                "time_on_ground": {"bronze": 0.7, "silver": 0.65, "gold": 0.6, "platinum": 0.55, "diamond": 0.5}
            },
            "boost_management": {
                "boost_efficiency": {"bronze": 50, "silver": 75, "gold": 100, "platinum": 125, "diamond": 150}
            },
            "aerial_ability": {
                "aerial_tendency": {"bronze": 0.1, "silver": 0.15, "gold": 0.2, "platinum": 0.25, "diamond": 0.3},
                "time_high_air": {"bronze": 0.05, "silver": 0.08, "gold": 0.12, "platinum": 0.15, "diamond": 0.2}
            }
        }
    
    def analyze_player_skills(self, matches: List[Match]) -> Dict[str, Any]:
        """
        Comprehensive skill analysis for a player.
        
        Args:
            matches: Player's matches for analysis
            
        Returns:
            Detailed skill analysis report
        """
        try:
            if not matches:
                return {"error": "No matches provided for analysis"}
            
            logger.info("Analyzing player skills", matches=len(matches))
            
            # Extract features
            features_df = self.feature_pipeline.extract_features_from_matches(matches)
            
            if features_df.empty:
                return {"error": "No features extracted from matches"}
            
            # Group features by skill category
            skill_features = create_skill_category_features(features_df)
            
            # Analyze each skill category
            skill_analysis = {}
            for category, category_df in skill_features.items():
                if not category_df.empty:
                    skill_analysis[category] = self._analyze_skill_category(
                        category, category_df, matches
                    )
            
            # Calculate overall performance metrics
            overall_metrics = self._calculate_overall_metrics(features_df, matches)
            
            # Identify strengths and weaknesses
            strengths_weaknesses = self._identify_strengths_weaknesses(skill_analysis)
            
            # Generate improvement trends
            improvement_trends = self._calculate_improvement_trends(features_df)
            
            analysis_report = {
                "player_summary": {
                    "total_matches": len(matches),
                    "analysis_period": {
                        "start_date": min(m.match_date for m in matches).isoformat(),
                        "end_date": max(m.match_date for m in matches).isoformat()
                    },
                    "overall_performance": overall_metrics
                },
                "skill_categories": skill_analysis,
                "strengths_and_weaknesses": strengths_weaknesses,
                "improvement_trends": improvement_trends,
                "recommendations": self._generate_skill_recommendations(skill_analysis, strengths_weaknesses)
            }
            
            logger.info("Player skill analysis completed",
                       categories_analyzed=len(skill_analysis),
                       strengths=len(strengths_weaknesses.get("strengths", [])),
                       weaknesses=len(strengths_weaknesses.get("weaknesses", [])))
            
            return analysis_report
            
        except Exception as e:
            logger.error("Failed to analyze player skills", error=str(e))
            return {"error": str(e)}
    
    def _analyze_skill_category(self, 
                               category: str, 
                               category_df: pd.DataFrame,
                               matches: List[Match]) -> Dict[str, Any]:
        """Analyze a specific skill category."""
        try:
            analysis = {
                "category_name": category,
                "features_analyzed": list(category_df.columns),
                "performance_metrics": {},
                "percentile_rankings": {},
                "trend_analysis": {},
                "category_score": 0.0
            }
            
            # Calculate performance metrics for each feature
            for feature in category_df.columns:
                feature_values = category_df[feature].dropna()
                
                if len(feature_values) > 0:
                    metrics = {
                        "current_value": float(feature_values.iloc[-1]) if len(feature_values) > 0 else 0.0,
                        "average": float(feature_values.mean()),
                        "std_dev": float(feature_values.std()) if len(feature_values) > 1 else 0.0,
                        "min": float(feature_values.min()),
                        "max": float(feature_values.max()),
                        "trend": self._calculate_feature_trend(feature_values)
                    }
                    
                    analysis["performance_metrics"][feature] = metrics
                    
                    # Calculate percentile ranking
                    percentile = self._calculate_percentile_ranking(category, feature, metrics["current_value"])
                    analysis["percentile_rankings"][feature] = percentile
            
            # Calculate overall category score
            if analysis["percentile_rankings"]:
                analysis["category_score"] = float(np.mean(list(analysis["percentile_rankings"].values())))
            
            # Trend analysis for the category
            if len(category_df) > 1:
                analysis["trend_analysis"] = self._analyze_category_trend(category_df)
            
            return analysis
            
        except Exception as e:
            logger.error("Failed to analyze skill category", category=category, error=str(e))
            return {"error": str(e)}
    
    def _calculate_feature_trend(self, values: pd.Series) -> Dict[str, Any]:
        """Calculate trend for a feature over time."""
        if len(values) < 2:
            return {"direction": "insufficient_data", "slope": 0.0, "confidence": 0.0}
        
        try:
            # Linear regression for trend
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Determine trend direction
            if abs(slope) < std_err:
                direction = "stable"
            elif slope > 0:
                direction = "improving"
            else:
                direction = "declining"
            
            return {
                "direction": direction,
                "slope": float(slope),
                "confidence": float(abs(r_value)),  # Correlation coefficient as confidence
                "p_value": float(p_value)
            }
            
        except Exception:
            return {"direction": "unknown", "slope": 0.0, "confidence": 0.0}
    
    def _calculate_percentile_ranking(self, 
                                    category: str, 
                                    feature: str, 
                                    value: float) -> float:
        """Calculate percentile ranking for a feature value."""
        # This is a simplified implementation
        # In production, this would use population data
        
        if category in self.performance_benchmarks and feature in self.performance_benchmarks[category]:
            benchmarks = self.performance_benchmarks[category][feature]
            
            # Find percentile based on rank benchmarks
            if value >= benchmarks.get("diamond", 0):
                return 90.0
            elif value >= benchmarks.get("platinum", 0):
                return 75.0
            elif value >= benchmarks.get("gold", 0):
                return 50.0
            elif value >= benchmarks.get("silver", 0):
                return 25.0
            else:
                return 10.0
        
        # Default percentile calculation
        return 50.0  # Assume average if no benchmarks
    
    def _analyze_category_trend(self, category_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall trend for a skill category."""
        try:
            # Calculate average performance over time
            avg_performance = category_df.mean(axis=1)
            
            if len(avg_performance) < 2:
                return {"trend": "insufficient_data"}
            
            # Recent vs historical comparison
            recent_window = min(self.trend_window, len(avg_performance))
            recent_avg = avg_performance.tail(recent_window).mean()
            historical_avg = avg_performance.head(-recent_window).mean() if len(avg_performance) > recent_window else recent_avg
            
            improvement = recent_avg - historical_avg
            improvement_percentage = (improvement / max(abs(historical_avg), 0.001)) * 100
            
            return {
                "trend": "improving" if improvement > 0 else "declining" if improvement < 0 else "stable",
                "improvement_value": float(improvement),
                "improvement_percentage": float(improvement_percentage),
                "recent_average": float(recent_avg),
                "historical_average": float(historical_avg)
            }
            
        except Exception as e:
            logger.error("Failed to analyze category trend", error=str(e))
            return {"trend": "unknown"}
    
    def _calculate_overall_metrics(self, features_df: pd.DataFrame, matches: List[Match]) -> Dict[str, Any]:
        """Calculate overall performance metrics."""
        try:
            # Basic match statistics
            total_goals = sum(m.goals for m in matches)
            total_assists = sum(m.assists for m in matches)
            total_saves = sum(m.saves for m in matches)
            total_shots = sum(m.shots for m in matches)
            
            wins = len([m for m in matches if m.result == "win"])
            losses = len([m for m in matches if m.result == "loss"])
            
            return {
                "win_rate": float(wins / len(matches)) if matches else 0.0,
                "average_score": float(np.mean([m.score for m in matches])) if matches else 0.0,
                "goals_per_match": float(total_goals / len(matches)) if matches else 0.0,
                "assists_per_match": float(total_assists / len(matches)) if matches else 0.0,
                "saves_per_match": float(total_saves / len(matches)) if matches else 0.0,
                "shot_accuracy": float(total_goals / max(total_shots, 1)),
                "consistency_score": float(1.0 - (np.std([m.score for m in matches]) / max(np.mean([m.score for m in matches]), 1))) if len(matches) > 1 else 1.0
            }
            
        except Exception as e:
            logger.error("Failed to calculate overall metrics", error=str(e))
            return {}
    
    def _identify_strengths_weaknesses(self, skill_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Identify player strengths and weaknesses."""
        try:
            category_scores = {}
            
            for category, analysis in skill_analysis.items():
                if isinstance(analysis, dict) and "category_score" in analysis:
                    category_scores[category] = analysis["category_score"]
            
            if not category_scores:
                return {"strengths": [], "weaknesses": [], "balanced_areas": []}
            
            # Sort categories by score
            sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Identify strengths (top 25%) and weaknesses (bottom 25%)
            n_categories = len(sorted_categories)
            strength_threshold = max(1, n_categories // 4)
            weakness_threshold = max(1, n_categories // 4)
            
            strengths = [cat for cat, score in sorted_categories[:strength_threshold] if score >= 70]
            weaknesses = [cat for cat, score in sorted_categories[-weakness_threshold:] if score <= 40]
            balanced_areas = [cat for cat, score in sorted_categories if 40 < score < 70]
            
            return {
                "strengths": strengths,
                "weaknesses": weaknesses,
                "balanced_areas": balanced_areas,
                "category_scores": category_scores
            }
            
        except Exception as e:
            logger.error("Failed to identify strengths and weaknesses", error=str(e))
            return {"strengths": [], "weaknesses": [], "balanced_areas": []}
    
    def _calculate_improvement_trends(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate improvement trends across all features."""
        try:
            if len(features_df) < 2:
                return {"overall_trend": "insufficient_data"}
            
            # Calculate trends for key performance indicators
            key_features = ["goals", "assists", "saves", "shot_accuracy", "score"]
            available_features = [f for f in key_features if f in features_df.columns]
            
            trends = {}
            for feature in available_features:
                feature_trend = self._calculate_feature_trend(features_df[feature])
                trends[feature] = feature_trend
            
            # Overall improvement assessment
            improving_features = len([t for t in trends.values() if t["direction"] == "improving"])
            declining_features = len([t for t in trends.values() if t["direction"] == "declining"])
            
            if improving_features > declining_features:
                overall_trend = "improving"
            elif declining_features > improving_features:
                overall_trend = "declining"
            else:
                overall_trend = "stable"
            
            return {
                "overall_trend": overall_trend,
                "feature_trends": trends,
                "improving_features": improving_features,
                "declining_features": declining_features,
                "stable_features": len(trends) - improving_features - declining_features
            }
            
        except Exception as e:
            logger.error("Failed to calculate improvement trends", error=str(e))
            return {"overall_trend": "unknown"}
    
    def _generate_skill_recommendations(self, 
                                      skill_analysis: Dict[str, Any],
                                      strengths_weaknesses: Dict[str, Any]) -> List[str]:
        """Generate skill-specific recommendations."""
        recommendations = []
        
        # Focus on weaknesses
        for weakness in strengths_weaknesses.get("weaknesses", []):
            if weakness == "mechanical":
                recommendations.append("Focus on fundamental mechanics: ball control, car control, and consistent touches.")
            elif weakness == "shooting":
                recommendations.append("Practice shooting accuracy with training packs and free play sessions.")
            elif weakness == "defending":
                recommendations.append("Work on defensive positioning and save consistency training.")
            elif weakness == "boost_management":
                recommendations.append("Practice boost collection routes and efficiency drills.")
            elif weakness == "positioning":
                recommendations.append("Study rotation patterns and practice positioning in different scenarios.")
            elif weakness == "aerial_ability":
                recommendations.append("Focus on aerial training packs and air roll control exercises.")
            elif weakness == "game_sense":
                recommendations.append("Work on decision-making and game awareness through replay analysis.")
        
        # Leverage strengths
        strengths = strengths_weaknesses.get("strengths", [])
        if strengths:
            recommendations.append(f"Continue to leverage your strengths in {', '.join(strengths)} while addressing weaker areas.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Continue practicing consistently to maintain and improve your current skill level.")
        
        return recommendations
