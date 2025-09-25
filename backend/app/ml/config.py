"""
ML Configuration and Settings

Centralized configuration for machine learning components including
model parameters, feature engineering settings, and evaluation metrics.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field
from enum import Enum


class SkillCategory(str, Enum):
    """Player skill categories for weakness detection."""
    MECHANICAL = "mechanical"
    POSITIONING = "positioning"
    GAME_SENSE = "game_sense"
    BOOST_MANAGEMENT = "boost_management"
    ROTATION = "rotation"
    AERIAL_ABILITY = "aerial_ability"
    SHOOTING = "shooting"
    DEFENDING = "defending"


class MLConfig(BaseModel):
    """Machine Learning configuration settings."""
    
    # Model Parameters
    weakness_detection_model: str = Field(default="random_forest", description="Model type for weakness detection")
    recommendation_model: str = Field(default="collaborative_filtering", description="Model type for recommendations")
    
    # Feature Engineering
    feature_window_size: int = Field(default=10, description="Number of recent matches for feature calculation")
    min_matches_required: int = Field(default=5, description="Minimum matches needed for analysis")
    
    # Model Training
    test_size: float = Field(default=0.2, description="Test set size for model validation")
    random_state: int = Field(default=42, description="Random state for reproducibility")
    cross_validation_folds: int = Field(default=5, description="Number of CV folds")
    
    # Performance Thresholds
    min_accuracy_threshold: float = Field(default=0.8, description="Minimum required model accuracy")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence for predictions")
    
    # Skill Categories and Weights
    skill_categories: List[SkillCategory] = Field(
        default=[
            SkillCategory.MECHANICAL,
            SkillCategory.POSITIONING, 
            SkillCategory.GAME_SENSE,
            SkillCategory.BOOST_MANAGEMENT,
            SkillCategory.ROTATION,
            SkillCategory.AERIAL_ABILITY,
            SkillCategory.SHOOTING,
            SkillCategory.DEFENDING
        ],
        description="Available skill categories for analysis"
    )
    
    # Feature Weights for Different Skill Categories
    feature_weights: Dict[str, Dict[str, float]] = Field(
        default={
            "mechanical": {
                "shots": 0.3,
                "saves": 0.2,
                "goals": 0.25,
                "assists": 0.15,
                "score": 0.1
            },
            "positioning": {
                "boost_usage": 0.4,
                "time_in_attacking_third": 0.3,
                "time_in_defensive_third": 0.3
            },
            "game_sense": {
                "assists": 0.4,
                "saves": 0.3,
                "boost_efficiency": 0.3
            }
        },
        description="Feature importance weights for each skill category"
    )
    
    # Model Hyperparameters
    random_forest_params: Dict[str, Any] = Field(
        default={
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 5,
            "min_samples_leaf": 2,
            "random_state": 42
        },
        description="Random Forest hyperparameters"
    )
    
    clustering_params: Dict[str, Any] = Field(
        default={
            "n_clusters": 8,
            "random_state": 42,
            "n_init": 10
        },
        description="K-Means clustering parameters"
    )


# Global ML configuration instance
ml_config = MLConfig()
