"""
Training Recommendation Engine for RocketTrainer.

This module implements personalized training pack recommendations based on:
1. Detected player weaknesses from WeaknessDetector
2. Player skill level and performance history
3. Training pack effectiveness and user ratings
4. Collaborative filtering based on similar players
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import structlog

from app.models.match import Match
from app.models.training_pack import TrainingPack
from app.models.training_session import TrainingSession
from app.models.user import User
from ..config import ml_config, SkillCategory
from ..utils import PerformanceMonitor
from .base import BaseMLModel

logger = structlog.get_logger()
performance_monitor = PerformanceMonitor()


class TrainingRecommendationEngine(BaseMLModel):
    """
    Intelligent training pack recommendation engine.
    
    Uses multiple recommendation strategies:
    1. Content-based filtering (weakness → training pack mapping)
    2. Collaborative filtering (similar players' preferences)
    3. Performance-based ranking (effectiveness for skill improvement)
    4. Difficulty matching (appropriate challenge level)
    """
    
    def __init__(self, db_session: Session):
        super().__init__(model_name="TrainingRecommendationEngine", model_version="1.0.0")
        self.db = db_session
        self.scaler = StandardScaler()
        
        # Weakness to category mapping
        self.weakness_mapping = {
            "mechanical": ["shooting", "dribbling", "aerials"],
            "positioning": ["positioning", "saves"],
            "game_sense": ["positioning", "saves", "shooting"],
            "boost_management": ["dribbling", "positioning"],
            "rotation": ["positioning", "saves"],
            "aerial_ability": ["aerials", "wall_play"],
            "shooting": ["shooting", "dribbling"],
            "defending": ["saves", "positioning"]
        }
        
        # Skill level progression
        self.skill_levels = ["bronze", "silver", "gold", "platinum", "diamond", "champion", "grand_champion"]
        
        logger.info("TrainingRecommendationEngine initialized", 
                   weakness_categories=len(self.weakness_mapping),
                   skill_levels=len(self.skill_levels))
    
    def _prepare_features(self, data: Any) -> np.ndarray:
        """Prepare features for recommendation (not used in this implementation)."""
        return np.array([])
    
    def _prepare_targets(self, data: Any) -> np.ndarray:
        """Prepare targets for recommendation (not used in this implementation)."""
        return np.array([])

    def _create_model(self) -> Any:
        """Create model (not used in this implementation - uses rule-based approach)."""
        return None
    
    def recommend_training_packs(
        self, 
        user_id: str,
        weaknesses: List[Dict[str, Any]], 
        player_skill_level: str = "platinum",
        max_recommendations: int = 5,
        include_variety: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized training pack recommendations.
        
        Args:
            user_id: User identifier
            weaknesses: List of detected weaknesses with confidence scores
            player_skill_level: Player's current skill level
            max_recommendations: Maximum number of recommendations to return
            include_variety: Whether to include variety in recommendations
            
        Returns:
            List of recommended training packs with scores and reasoning
        """
        logger.debug("Generating training recommendations", 
                    user_id=user_id,
                    weaknesses=len(weaknesses),
                    skill_level=player_skill_level,
                    max_recommendations=max_recommendations)
        
        try:
            # Get all available training packs
            training_packs = self._get_available_training_packs()
            
            if not training_packs:
                logger.warning("No training packs available for recommendations")
                return []
            
            # Calculate recommendation scores for each pack
            pack_scores = []
            
            for pack in training_packs:
                score_data = self._calculate_pack_score(
                    pack, weaknesses, player_skill_level, user_id
                )
                if score_data["total_score"] > 0:
                    pack_scores.append(score_data)
            
            # Sort by total score and apply diversity if requested
            pack_scores.sort(key=lambda x: x["total_score"], reverse=True)
            
            if include_variety:
                pack_scores = self._apply_diversity_filter(pack_scores, max_recommendations)
            
            # Return top recommendations
            recommendations = pack_scores[:max_recommendations]
            
            logger.info("Training recommendations generated",
                       user_id=user_id,
                       total_packs_evaluated=len(training_packs),
                       recommendations_generated=len(recommendations),
                       avg_score=np.mean([r["total_score"] for r in recommendations]) if recommendations else 0)
            
            return recommendations
            
        except Exception as e:
            logger.error("Failed to generate training recommendations", 
                        user_id=user_id, error=str(e))
            return []
    
    def _get_available_training_packs(self) -> List[TrainingPack]:
        """Get all available training packs from database."""
        return (self.db.query(TrainingPack)
                .filter(TrainingPack.is_active == True)
                .all())
    
    def _calculate_pack_score(
        self, 
        pack: TrainingPack, 
        weaknesses: List[Dict[str, Any]], 
        player_skill_level: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Calculate recommendation score for a training pack.
        
        Scoring components:
        1. Weakness relevance (40%)
        2. Difficulty appropriateness (25%)
        3. Pack quality/rating (20%)
        4. User history/preferences (15%)
        """
        scores = {
            "pack": pack,
            "weakness_score": 0.0,
            "difficulty_score": 0.0,
            "quality_score": 0.0,
            "preference_score": 0.0,
            "total_score": 0.0,
            "reasoning": []
        }
        
        # 1. Weakness relevance score (40% weight)
        weakness_score = self._calculate_weakness_relevance(pack, weaknesses)
        scores["weakness_score"] = weakness_score
        
        # 2. Difficulty appropriateness (25% weight)
        difficulty_score = self._calculate_difficulty_match(pack, player_skill_level)
        scores["difficulty_score"] = difficulty_score
        
        # 3. Pack quality score (20% weight)
        quality_score = self._calculate_quality_score(pack)
        scores["quality_score"] = quality_score
        
        # 4. User preference score (15% weight)
        preference_score = self._calculate_user_preference(pack, user_id)
        scores["preference_score"] = preference_score
        
        # Calculate weighted total score
        scores["total_score"] = (
            weakness_score * 0.40 +
            difficulty_score * 0.25 +
            quality_score * 0.20 +
            preference_score * 0.15
        )
        
        # Generate reasoning
        scores["reasoning"] = self._generate_reasoning(pack, weaknesses, scores)
        
        return scores
    
    def _calculate_weakness_relevance(
        self, 
        pack: TrainingPack, 
        weaknesses: List[Dict[str, Any]]
    ) -> float:
        """Calculate how relevant this pack is to detected weaknesses."""
        if not weaknesses:
            return 0.0
        
        relevance_score = 0.0
        
        for weakness in weaknesses:
            weakness_category = weakness.get("category", "")
            confidence = weakness.get("confidence", 0.0)
            
            # Check if pack category matches weakness
            if weakness_category in self.weakness_mapping:
                relevant_categories = self.weakness_mapping[weakness_category]
                
                if pack.category in relevant_categories:
                    # Direct category match
                    relevance_score += confidence * 1.0
                elif any(cat in pack.tags or [] for cat in relevant_categories):
                    # Tag match
                    relevance_score += confidence * 0.7
                elif pack.subcategory and any(cat in pack.subcategory for cat in relevant_categories):
                    # Subcategory match
                    relevance_score += confidence * 0.5
        
        return min(relevance_score, 1.0)  # Cap at 1.0
    
    def _calculate_difficulty_match(self, pack: TrainingPack, player_skill_level: str) -> float:
        """Calculate how well pack difficulty matches player skill level."""
        try:
            player_level_idx = self.skill_levels.index(player_skill_level.lower())
        except ValueError:
            player_level_idx = 3  # Default to platinum
        
        try:
            pack_level_idx = self.skill_levels.index(pack.skill_level.lower())
        except ValueError:
            pack_level_idx = 3  # Default to platinum
        
        # Calculate difficulty appropriateness
        level_diff = abs(player_level_idx - pack_level_idx)
        
        if level_diff == 0:
            return 1.0  # Perfect match
        elif level_diff == 1:
            return 0.8  # Close match
        elif level_diff == 2:
            return 0.5  # Moderate match
        else:
            return 0.2  # Poor match
    
    def _calculate_quality_score(self, pack: TrainingPack) -> float:
        """Calculate pack quality score based on ratings and usage."""
        quality_score = 0.0
        
        # Rating component (0-1 scale)
        if pack.rating and pack.rating_count > 0:
            # Normalize rating from 0-5 to 0-1
            rating_score = pack.rating / 5.0
            
            # Weight by number of ratings (more ratings = more reliable)
            rating_weight = min(pack.rating_count / 1000.0, 1.0)
            quality_score += rating_score * rating_weight * 0.7
        
        # Usage popularity component
        if pack.usage_count > 0:
            # Normalize usage (log scale to prevent extreme values)
            usage_score = min(np.log10(pack.usage_count + 1) / 4.0, 1.0)
            quality_score += usage_score * 0.3
        
        # Bonus for official/featured packs
        if pack.is_official:
            quality_score += 0.1
        if pack.is_featured:
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _calculate_user_preference(self, pack: TrainingPack, user_id: str) -> float:
        """Calculate user preference score based on training history."""
        try:
            # Get user's training history
            user_sessions = (self.db.query(TrainingSession)
                           .filter(TrainingSession.user_id == user_id)
                           .all())
            
            if not user_sessions:
                return 0.5  # Neutral score for new users
            
            # Analyze user preferences
            category_preferences = {}
            total_sessions = len(user_sessions)
            
            for session in user_sessions:
                if session.training_pack and session.training_pack.category:
                    category = session.training_pack.category
                    if category not in category_preferences:
                        category_preferences[category] = 0
                    category_preferences[category] += 1
            
            # Calculate preference score for this pack's category
            if pack.category in category_preferences:
                preference_ratio = category_preferences[pack.category] / total_sessions
                return min(preference_ratio * 2.0, 1.0)  # Scale up preference
            
            return 0.3  # Low score for untried categories
            
        except Exception as e:
            logger.warning("Failed to calculate user preference", 
                          user_id=user_id, error=str(e))
            return 0.5
    
    def _apply_diversity_filter(
        self, 
        pack_scores: List[Dict[str, Any]], 
        max_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Apply diversity filter to avoid recommending too many similar packs."""
        if len(pack_scores) <= max_recommendations:
            return pack_scores
        
        diverse_recommendations = []
        used_categories = set()
        
        # First pass: select top pack from each category
        for pack_data in pack_scores:
            pack = pack_data["pack"]
            if pack.category not in used_categories:
                diverse_recommendations.append(pack_data)
                used_categories.add(pack.category)
                
                if len(diverse_recommendations) >= max_recommendations:
                    break
        
        # Second pass: fill remaining slots with highest scoring packs
        remaining_slots = max_recommendations - len(diverse_recommendations)
        if remaining_slots > 0:
            for pack_data in pack_scores:
                if pack_data not in diverse_recommendations:
                    diverse_recommendations.append(pack_data)
                    remaining_slots -= 1
                    if remaining_slots == 0:
                        break
        
        return diverse_recommendations
    
    def _generate_reasoning(
        self, 
        pack: TrainingPack, 
        weaknesses: List[Dict[str, Any]], 
        scores: Dict[str, Any]
    ) -> List[str]:
        """Generate human-readable reasoning for the recommendation."""
        reasoning = []
        
        # Weakness relevance reasoning
        if scores["weakness_score"] > 0.7:
            relevant_weaknesses = [w["category"] for w in weaknesses 
                                 if w["category"] in self.weakness_mapping and 
                                 pack.category in self.weakness_mapping[w["category"]]]
            if relevant_weaknesses:
                reasoning.append(f"Directly addresses your weakness in {', '.join(relevant_weaknesses)}")
        
        # Difficulty reasoning
        if scores["difficulty_score"] > 0.8:
            reasoning.append(f"Perfect difficulty match for your skill level")
        elif scores["difficulty_score"] > 0.6:
            reasoning.append(f"Good difficulty progression for improvement")
        
        # Quality reasoning
        if scores["quality_score"] > 0.8:
            reasoning.append(f"Highly rated pack ({pack.rating:.1f}/5.0 from {pack.rating_count} users)")
        
        # Special features
        if pack.is_official:
            reasoning.append("Official Psyonix training pack")
        if pack.is_featured:
            reasoning.append("Community featured pack")
        
        return reasoning
