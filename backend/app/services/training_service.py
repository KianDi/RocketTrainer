"""
Training service for managing training recommendations and progress tracking.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import structlog

from app.models.user import User
from app.models.training_pack import TrainingPack
from app.models.training_session import TrainingSession
from app.models.match import Match
from app.schemas.training import TrainingRecommendation, TrainingPackResponse

logger = structlog.get_logger()


class TrainingService:
    """Service for training recommendations and progress tracking."""
    
    @staticmethod
    async def get_recommendations(user_id: str, db: Session) -> List[TrainingRecommendation]:
        """Get personalized training pack recommendations for a user."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            
            # Get user's recent matches to analyze weaknesses
            recent_matches = db.query(Match).filter(
                Match.user_id == user_id,
                Match.processed == True
            ).order_by(desc(Match.created_at)).limit(10).all()
            
            # Get user's training history
            training_history = db.query(TrainingSession).filter(
                TrainingSession.user_id == user_id
            ).order_by(desc(TrainingSession.completed_at)).limit(20).all()
            
            # Analyze weaknesses (simplified for MVP)
            weaknesses = TrainingService._analyze_weaknesses(recent_matches)
            
            # Get training packs that address these weaknesses
            recommendations = []
            
            for weakness, confidence in weaknesses.items():
                # Find training packs for this weakness category
                packs = db.query(TrainingPack).filter(
                    TrainingPack.category == weakness,
                    TrainingPack.is_active == True
                ).order_by(desc(TrainingPack.rating)).limit(3).all()
                
                for i, pack in enumerate(packs):
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
                        reason=f"Improve your {weakness} skills",
                        confidence=confidence,
                        priority=i + 1,
                        weakness_addressed=weakness,
                        expected_improvement=confidence * 0.1  # Mock improvement estimate
                    )
                    recommendations.append(recommendation)
            
            # Sort by confidence and priority
            recommendations.sort(key=lambda x: (x.confidence, -x.priority), reverse=True)
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error("Failed to get training recommendations", user_id=user_id, error=str(e))
            return []
    
    @staticmethod
    async def get_user_progress(user_id: str, db: Session) -> Dict[str, Any]:
        """Get user's training progress and statistics."""
        try:
            # Get all training sessions
            sessions = db.query(TrainingSession).filter(
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
