"""
Training Service for RocketTrainer.

Provides comprehensive training pack management and recommendation services.
Integrates with ML models to provide personalized training recommendations.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import structlog

from app.models.training_pack import TrainingPack
from app.models.training_session import TrainingSession
from app.models.match import Match
from app.models.user import User
from app.schemas.training import TrainingRecommendation, TrainingPackResponse
from app.ml.models.weakness_detector import WeaknessDetector
from app.ml.models.skill_analyzer import SkillAnalyzer
from app.ml.models.recommendation_engine import TrainingRecommendationEngine

logger = structlog.get_logger()


class TrainingService:
    """
    Service for managing training packs and generating recommendations.

    Provides:
    1. Training pack discovery and filtering
    2. Personalized recommendations based on ML analysis
    3. Training session tracking and progress analysis
    4. Performance improvement measurement
    """

    def __init__(self, db: Session):
        self.db = db
        self.weakness_detector = None
        self.skill_analyzer = None
        self.recommendation_engine = None

        logger.info("TrainingService initialized")

    async def get_recommendations(self, user_id: str) -> List[TrainingRecommendation]:
        """Get personalized training pack recommendations using ML analysis."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return []

            # Get user's recent matches for ML analysis
            recent_matches = self._get_user_recent_matches(user_id, limit=10)

            if not recent_matches:
                logger.warning("No recent matches found for user", user_id=user_id)
                return await self._get_default_recommendations()

            # Initialize ML models if needed
            if not self.weakness_detector:
                self.weakness_detector = WeaknessDetector()
                self.weakness_detector.train(recent_matches)

            if not self.skill_analyzer:
                self.skill_analyzer = SkillAnalyzer()

            if not self.recommendation_engine:
                self.recommendation_engine = TrainingRecommendationEngine(self.db)

            # Analyze player weaknesses using ML
            weakness_analysis = self.weakness_detector.predict(recent_matches[:5])
            skill_analysis = self.skill_analyzer.analyze_player_skills(recent_matches)

            # Determine player skill level
            player_skill_level = self._estimate_player_skill_level(recent_matches, skill_analysis)

            # Generate ML-powered recommendations
            ml_recommendations = self.recommendation_engine.recommend_training_packs(
                user_id=user_id,
                weaknesses=weakness_analysis,
                player_skill_level=player_skill_level,
                max_recommendations=5,
                include_variety=True
            )

            # Convert to TrainingRecommendation format
            recommendations = []
            for i, rec in enumerate(ml_recommendations):
                pack = rec["pack"]
                recommendation = TrainingRecommendation(
                    training_pack=TrainingPackResponse(
                        id=str(pack.id),
                        name=pack.name,
                        code=pack.code,
                        description=pack.description,
                        creator=pack.creator,
                        category=pack.category,
                        subcategory=pack.subcategory,
                        difficulty=pack.difficulty,
                        skill_level=pack.skill_level,
                        tags=pack.tags or [],
                        shots_count=pack.shots_count,
                        estimated_duration=pack.estimated_duration,
                        rating=pack.rating,
                        rating_count=pack.rating_count,
                        usage_count=pack.usage_count,
                        is_official=pack.is_official,
                        is_featured=pack.is_featured
                    ),
                    reason="; ".join(rec["reasoning"]) if rec["reasoning"] else f"Recommended for skill improvement",
                    confidence=rec["total_score"],
                    priority=i + 1,
                    weakness_addressed=weakness_analysis[0]["category"] if weakness_analysis else "general",
                    expected_improvement=rec["total_score"] * 0.15  # Estimated improvement based on score
                )
                recommendations.append(recommendation)

            logger.info("ML-powered recommendations generated",
                       user_id=user_id,
                       recommendations_count=len(recommendations),
                       weaknesses_detected=len(weakness_analysis))

            return recommendations
            
        except Exception as e:
            logger.error("Failed to get training recommendations", user_id=user_id, error=str(e))
            return await self._get_default_recommendations()

    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's training progress and statistics."""
        try:
            # Get all training sessions
            sessions = self.db.query(TrainingSession).filter(
                TrainingSession.user_id == user_id
            ).all()
            
            if not sessions:
                return {
                    "total_sessions": 0,
                    "total_duration": 0,
                    "average_accuracy": 0.0,
                    "improvement_rate": 0.0,
                    "favorite_categories": [],
                    "progress_by_category": {}
                }
            
            # Calculate basic stats
            total_sessions = len(sessions)
            total_duration = sum(session.duration for session in sessions)
            average_accuracy = sum(session.accuracy for session in sessions) / total_sessions
            
            # Calculate improvement rate (simplified)
            recent_sessions = sorted(sessions, key=lambda x: x.completed_at)[-10:]
            old_sessions = sorted(sessions, key=lambda x: x.completed_at)[:10]
            
            if old_sessions and recent_sessions:
                old_avg = sum(s.accuracy for s in old_sessions) / len(old_sessions)
                recent_avg = sum(s.accuracy for s in recent_sessions) / len(recent_sessions)
                improvement_rate = ((recent_avg - old_avg) / old_avg) * 100 if old_avg > 0 else 0
            else:
                improvement_rate = 0.0
            
            # Find favorite categories
            category_counts = {}
            for session in sessions:
                category = session.training_pack.category
                category_counts[category] = category_counts.get(category, 0) + 1
            
            favorite_categories = sorted(category_counts.keys(), 
                                       key=lambda x: category_counts[x], 
                                       reverse=True)[:3]
            
            # Progress by category
            progress_by_category = {}
            for category in category_counts.keys():
                category_sessions = [s for s in sessions if s.training_pack.category == category]
                if category_sessions:
                    progress_by_category[category] = {
                        "sessions": len(category_sessions),
                        "average_accuracy": sum(s.accuracy for s in category_sessions) / len(category_sessions),
                        "total_duration": sum(s.duration for s in category_sessions),
                        "best_accuracy": max(s.accuracy for s in category_sessions)
                    }
            
            return {
                "total_sessions": total_sessions,
                "total_duration": total_duration,
                "average_accuracy": round(average_accuracy, 2),
                "improvement_rate": round(improvement_rate, 2),
                "favorite_categories": favorite_categories,
                "progress_by_category": progress_by_category
            }
            
        except Exception as e:
            logger.error("Failed to get user progress", user_id=user_id, error=str(e))
            return {}

    def _get_user_recent_matches(self, user_id: str, limit: int = 10) -> List[Match]:
        """Get user's recent matches for analysis."""
        return (self.db.query(Match)
                .filter(Match.user_id == user_id)
                .filter(Match.processed == True)
                .order_by(Match.match_date.desc())
                .limit(limit)
                .all())

    def _estimate_player_skill_level(
        self,
        matches: List[Match],
        skill_analysis: Dict[str, Any]
    ) -> str:
        """Estimate player skill level based on performance."""
        if not matches:
            return "gold"

        # Simple heuristic based on average performance
        avg_score = sum(m.score for m in matches) / len(matches)
        avg_goals = sum(m.goals for m in matches) / len(matches)
        avg_saves = sum(m.saves for m in matches) / len(matches)

        # Score-based estimation (rough approximation)
        if avg_score > 800 and avg_goals > 2:
            return "champion"
        elif avg_score > 600 and avg_goals > 1.5:
            return "diamond"
        elif avg_score > 400 and avg_goals > 1:
            return "platinum"
        elif avg_score > 200:
            return "gold"
        else:
            return "silver"

    async def _get_default_recommendations(self) -> List[TrainingRecommendation]:
        """Get default recommendations for users without match history."""
        popular_packs = (self.db.query(TrainingPack)
                        .filter(TrainingPack.is_active == True)
                        .filter(TrainingPack.is_featured == True)
                        .order_by(TrainingPack.rating.desc())
                        .limit(5)
                        .all())

        recommendations = []
        for i, pack in enumerate(popular_packs):
            recommendation = TrainingRecommendation(
                training_pack=TrainingPackResponse(
                    id=str(pack.id),
                    name=pack.name,
                    code=pack.code,
                    description=pack.description,
                    creator=pack.creator,
                    category=pack.category,
                    subcategory=pack.subcategory,
                    difficulty=pack.difficulty,
                    skill_level=pack.skill_level,
                    tags=pack.tags or [],
                    shots_count=pack.shots_count,
                    estimated_duration=pack.estimated_duration,
                    rating=pack.rating,
                    rating_count=pack.rating_count,
                    usage_count=pack.usage_count,
                    is_official=pack.is_official,
                    is_featured=pack.is_featured
                ),
                reason="Popular community training pack",
                confidence=0.7,
                priority=i + 1,
                weakness_addressed="general",
                expected_improvement=0.1
            )
            recommendations.append(recommendation)

        return recommendations

    @staticmethod
    def _analyze_weaknesses(matches: List[Match]) -> Dict[str, float]:
        """
        Analyze user weaknesses from recent matches.
        This is a simplified version for MVP.
        """
        if not matches:
            return {"aerials": 0.8, "saves": 0.7, "shooting": 0.6}
        
        weaknesses = {}
        
        # Analyze save percentage
        total_saves = sum(match.saves or 0 for match in matches)
        total_shots_against = sum(match.score_team_1 + (match.saves or 0) for match in matches)
        
        if total_shots_against > 0:
            save_percentage = total_saves / total_shots_against
            if save_percentage < 0.6:  # Below 60% save rate
                weaknesses["saves"] = 0.8
        
        # Analyze shooting accuracy
        total_goals = sum(match.goals or 0 for match in matches)
        total_shots = sum(match.shots or 0 for match in matches)
        
        if total_shots > 0:
            shot_accuracy = total_goals / total_shots
            if shot_accuracy < 0.3:  # Below 30% shot accuracy
                weaknesses["shooting"] = 0.7
        
        # Analyze aerial play (mock analysis based on time in air)
        total_air_time = sum(
            (match.time_low_air or 0) + (match.time_high_air or 0) 
            for match in matches
        )
        total_match_time = sum(match.duration for match in matches)
        
        if total_match_time > 0:
            air_time_percentage = total_air_time / total_match_time
            if air_time_percentage < 0.15:  # Less than 15% time in air
                weaknesses["aerials"] = 0.9
        
        # Default weaknesses if no specific issues found
        if not weaknesses:
            weaknesses = {"positioning": 0.6, "rotation": 0.5}
        
        return weaknesses
