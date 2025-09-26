"""
Synthetic Training Data Generator for RocketTrainer ML Models

Generates realistic Rocket League gameplay data for training ML models
when real replay data is not available. Creates synthetic matches with
realistic statistics, skill distributions, and correlations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import uuid
import structlog
from dataclasses import dataclass
from enum import Enum

from ..config import SkillCategory, ml_config
from ...models.match import Match
from ...models.user import User

logger = structlog.get_logger(__name__)


class RankTier(Enum):
    """Rocket League rank tiers with skill level mappings."""
    BRONZE = ("Bronze", 0.1, 0.3)
    SILVER = ("Silver", 0.2, 0.4)
    GOLD = ("Gold", 0.3, 0.5)
    PLATINUM = ("Platinum", 0.4, 0.6)
    DIAMOND = ("Diamond", 0.5, 0.7)
    CHAMPION = ("Champion", 0.6, 0.8)
    GRAND_CHAMPION = ("Grand Champion", 0.7, 0.9)
    SUPERSONIC_LEGEND = ("Supersonic Legend", 0.8, 1.0)
    
    def __init__(self, display_name: str, min_skill: float, max_skill: float):
        self.display_name = display_name
        self.min_skill = min_skill
        self.max_skill = max_skill


@dataclass
class PlayerProfile:
    """Synthetic player profile with skill characteristics."""
    user_id: str
    username: str
    rank_tier: RankTier
    skill_levels: Dict[str, float]  # 0-1 scale for each skill category
    playstyle: str  # "aggressive", "defensive", "balanced"
    consistency: float  # 0-1, affects variance in performance
    improvement_rate: float  # How quickly skills improve over time


class SyntheticDataGenerator:
    """Generates synthetic Rocket League training data."""
    
    def __init__(self, random_seed: Optional[int] = None):
        """Initialize the synthetic data generator."""
        self.random_seed = random_seed or ml_config.random_state
        np.random.seed(self.random_seed)
        
        # Skill categories and their correlations
        self.skill_categories = [
            "mechanical", "positioning", "game_sense", "boost_management",
            "rotation", "aerial_ability", "shooting", "defending"
        ]
        
        # Define skill correlations (some skills are related)
        self.skill_correlations = {
            "mechanical": ["aerial_ability", "shooting"],
            "positioning": ["game_sense", "rotation", "defending"],
            "game_sense": ["positioning", "boost_management"],
            "aerial_ability": ["mechanical", "shooting"],
            "shooting": ["mechanical", "aerial_ability"],
            "defending": ["positioning", "game_sense"]
        }
        
        # Playstyle characteristics
        self.playstyle_modifiers = {
            "aggressive": {
                "shooting": 1.2, "aerial_ability": 1.1, "mechanical": 1.1,
                "defending": 0.9, "positioning": 0.9
            },
            "defensive": {
                "defending": 1.2, "positioning": 1.1, "game_sense": 1.1,
                "shooting": 0.9, "aerial_ability": 0.9
            },
            "balanced": {skill: 1.0 for skill in self.skill_categories}
        }
        
        logger.info("SyntheticDataGenerator initialized", 
                   seed=self.random_seed,
                   skill_categories=len(self.skill_categories))
    
    def generate_player_profiles(self, num_players: int = 1000) -> List[PlayerProfile]:
        """Generate synthetic player profiles with diverse characteristics."""
        profiles = []
        
        for i in range(num_players):
            # Select rank tier (weighted towards middle ranks)
            rank_weights = [0.05, 0.1, 0.15, 0.25, 0.25, 0.15, 0.04, 0.01]
            rank_tier = np.random.choice(list(RankTier), p=rank_weights)
            
            # Generate base skill level within rank range
            base_skill = np.random.uniform(rank_tier.min_skill, rank_tier.max_skill)
            
            # Select playstyle
            playstyle = np.random.choice(["aggressive", "defensive", "balanced"], 
                                       p=[0.3, 0.3, 0.4])
            
            # Generate skill levels with correlations
            skill_levels = self._generate_correlated_skills(base_skill, playstyle)
            
            # Generate player characteristics
            consistency = np.random.beta(2, 2)  # Most players have moderate consistency
            improvement_rate = np.random.exponential(0.02)  # Small positive improvement
            
            profile = PlayerProfile(
                user_id=str(uuid.uuid4()),
                username=f"player_{i:04d}",
                rank_tier=rank_tier,
                skill_levels=skill_levels,
                playstyle=playstyle,
                consistency=consistency,
                improvement_rate=improvement_rate
            )
            
            profiles.append(profile)
        
        logger.info("Generated player profiles", count=len(profiles))
        return profiles
    
    def _generate_correlated_skills(self, base_skill: float, playstyle: str) -> Dict[str, float]:
        """Generate skill levels with realistic correlations."""
        skills = {}
        
        # Start with base skill level
        for category in self.skill_categories:
            # Add some random variation
            variation = np.random.normal(0, 0.1)
            skill_level = np.clip(base_skill + variation, 0.0, 1.0)
            
            # Apply playstyle modifiers
            modifier = self.playstyle_modifiers[playstyle].get(category, 1.0)
            skill_level *= modifier
            
            skills[category] = np.clip(skill_level, 0.0, 1.0)
        
        # Apply correlations (correlated skills should be similar)
        for skill, correlated_skills in self.skill_correlations.items():
            if skill in skills:
                base_level = skills[skill]
                for corr_skill in correlated_skills:
                    if corr_skill in skills:
                        # Pull correlated skill towards base skill
                        correlation_strength = 0.3
                        current_level = skills[corr_skill]
                        adjusted_level = (current_level * (1 - correlation_strength) + 
                                        base_level * correlation_strength)
                        skills[corr_skill] = np.clip(adjusted_level, 0.0, 1.0)
        
        return skills
    
    def generate_match_data(self, 
                          player_profile: PlayerProfile,
                          num_matches: int = 50,
                          time_span_days: int = 30) -> List[Dict[str, Any]]:
        """Generate synthetic match data for a player."""
        matches = []
        
        # Generate matches over time span
        start_date = datetime.now() - timedelta(days=time_span_days)
        
        for i in range(num_matches):
            # Match timing (more matches on weekends)
            days_offset = np.random.uniform(0, time_span_days)
            match_date = start_date + timedelta(days=days_offset)
            
            # Apply skill improvement over time
            time_progress = days_offset / time_span_days
            skill_improvement = player_profile.improvement_rate * time_progress
            
            # Generate match performance based on skills
            match_stats = self._generate_match_performance(
                player_profile, skill_improvement, match_date
            )
            
            matches.append(match_stats)
        
        # Sort by date
        matches.sort(key=lambda x: x['match_date'])
        
        logger.debug("Generated match data", 
                    player=player_profile.username,
                    matches=len(matches))
        
        return matches
    
    def _generate_match_performance(self, 
                                  profile: PlayerProfile,
                                  skill_improvement: float,
                                  match_date: datetime) -> Dict[str, Any]:
        """Generate realistic match performance statistics."""
        # Apply consistency factor (affects performance variance)
        consistency_factor = profile.consistency
        performance_variance = (1 - consistency_factor) * 0.3
        
        # Current skill levels with improvement
        current_skills = {
            skill: min(1.0, level + skill_improvement)
            for skill, level in profile.skill_levels.items()
        }
        
        # Generate core statistics based on skills
        mechanical_skill = current_skills["mechanical"]
        shooting_skill = current_skills["shooting"]
        defending_skill = current_skills["defending"]
        positioning_skill = current_skills["positioning"]
        
        # Add performance variance
        def add_variance(base_value: float) -> float:
            variance = np.random.normal(0, performance_variance)
            return max(0, base_value + variance)
        
        # Generate match statistics
        match_duration = np.random.uniform(4.5, 7.0)  # minutes
        
        # Goals (based on shooting and mechanical skills)
        goals_rate = (shooting_skill * 0.7 + mechanical_skill * 0.3) * 1.5
        goals = int(np.random.poisson(add_variance(goals_rate)))
        
        # Shots (higher for aggressive players)
        shots_multiplier = 1.2 if profile.playstyle == "aggressive" else 1.0
        shots_rate = (shooting_skill * 0.6 + mechanical_skill * 0.4) * 8 * shots_multiplier
        shots = max(goals, int(np.random.poisson(add_variance(shots_rate))))
        
        # Saves (based on defending and positioning)
        saves_rate = (defending_skill * 0.8 + positioning_skill * 0.2) * 3
        saves = int(np.random.poisson(add_variance(saves_rate)))
        
        # Assists (based on game sense and positioning)
        assists_rate = (current_skills["game_sense"] * 0.6 + positioning_skill * 0.4) * 1.2
        assists = int(np.random.poisson(add_variance(assists_rate)))
        
        # Score (combination of all actions)
        base_score = goals * 100 + assists * 50 + saves * 50 + shots * 10
        score_bonus = int(np.random.uniform(0, 200))  # Random bonus points
        score = base_score + score_bonus
        
        # Win probability based on overall skill
        overall_skill = np.mean(list(current_skills.values()))
        win_probability = 0.3 + (overall_skill * 0.4)  # 30-70% win rate range
        is_win = np.random.random() < win_probability
        
        # Match result
        if is_win:
            result = "win"
        else:
            result = "loss" if np.random.random() < 0.8 else "draw"
        
        return {
            "user_id": profile.user_id,
            "match_date": match_date,
            "goals": goals,
            "assists": assists,
            "saves": saves,
            "shots": shots,
            "score": score,
            "match_duration_minutes": match_duration,
            "is_win": is_win,
            "result": result,
            "playlist": np.random.choice(["ranked_2v2", "ranked_3v3", "casual_2v2", "casual_3v3"]),
            "processed": True,
            # Store true skill levels for training labels
            "_true_skills": current_skills,
            "_player_profile": {
                "rank_tier": profile.rank_tier.display_name,
                "playstyle": profile.playstyle,
                "consistency": profile.consistency
            }
        }

    def create_training_dataset(self,
                              num_players: int = 500,
                              matches_per_player: int = 30) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
        """
        Create a complete training dataset with features and labels.

        Args:
            num_players: Number of synthetic players to generate
            matches_per_player: Number of matches per player

        Returns:
            Tuple of (features_df, labels_dict) where labels_dict contains
            weakness labels and skill category scores for training
        """
        logger.info("Creating synthetic training dataset",
                   players=num_players,
                   matches_per_player=matches_per_player)

        # Generate player profiles
        profiles = self.generate_player_profiles(num_players)

        # Generate match data for all players
        all_matches = []
        all_labels = {
            "primary_weakness": [],
            "skill_scores": [],
            "weakness_confidence": [],
            "player_ids": []
        }

        for profile in profiles:
            # Generate matches for this player
            matches = self.generate_match_data(profile, matches_per_player)
            all_matches.extend(matches)

            # Create training labels based on true skills
            primary_weakness = self._identify_primary_weakness(profile.skill_levels)
            skill_scores = list(profile.skill_levels.values())

            # Confidence based on skill variance (more varied skills = lower confidence)
            skill_variance = np.var(skill_scores)
            confidence = max(0.1, 1.0 - skill_variance * 2)

            # Add labels for each match (same player = same labels)
            for _ in matches:
                all_labels["primary_weakness"].append(primary_weakness)
                all_labels["skill_scores"].append(skill_scores)
                all_labels["weakness_confidence"].append(confidence)
                all_labels["player_ids"].append(profile.user_id)

        # Convert to DataFrame
        features_df = pd.DataFrame(all_matches)

        # Convert labels to numpy arrays
        labels_dict = {
            "primary_weakness": np.array(all_labels["primary_weakness"]),
            "skill_scores": np.array(all_labels["skill_scores"]),
            "weakness_confidence": np.array(all_labels["weakness_confidence"]),
            "player_ids": np.array(all_labels["player_ids"])
        }

        logger.info("Training dataset created",
                   total_matches=len(features_df),
                   unique_players=len(set(all_labels["player_ids"])),
                   features=len(features_df.columns))

        return features_df, labels_dict

    def _identify_primary_weakness(self, skill_levels: Dict[str, float]) -> str:
        """Identify the primary weakness (lowest skill) for a player."""
        # Find the skill with the lowest score
        min_skill = min(skill_levels.items(), key=lambda x: x[1])
        return min_skill[0]

    def save_training_data(self,
                          features_df: pd.DataFrame,
                          labels_dict: Dict[str, np.ndarray],
                          output_dir: str = "/tmp/ml_training_data") -> Dict[str, str]:
        """Save training data to files for model training."""
        import os

        os.makedirs(output_dir, exist_ok=True)

        # Save features
        features_path = os.path.join(output_dir, "training_features.csv")
        features_df.to_csv(features_path, index=False)

        # Save labels
        labels_path = os.path.join(output_dir, "training_labels.npz")
        np.savez(labels_path, **labels_dict)

        # Save metadata
        metadata = {
            "num_samples": len(features_df),
            "num_features": len(features_df.columns),
            "skill_categories": self.skill_categories,
            "generated_at": datetime.now().isoformat()
        }

        metadata_path = os.path.join(output_dir, "metadata.json")
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info("Training data saved",
                   features_path=features_path,
                   labels_path=labels_path,
                   metadata_path=metadata_path)

        return {
            "features": features_path,
            "labels": labels_path,
            "metadata": metadata_path
        }
