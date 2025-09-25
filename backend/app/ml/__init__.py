"""
RocketTrainer ML Package

This package contains machine learning models and utilities for:
- Weakness detection in Rocket League gameplay
- Training pack recommendations
- Player performance analysis
- Feature engineering and data preprocessing

Core Components:
- models/: ML model implementations
- features/: Feature engineering and data preprocessing
- evaluation/: Model evaluation and metrics
- utils/: ML utility functions and helpers
"""

__version__ = "1.0.0"
__author__ = "RocketTrainer Team"

# Import core ML components
from .config import MLConfig, ml_config, SkillCategory
from .utils import ModelManager, DataValidator, PerformanceMonitor
from .models.base import BaseMLModel
from .models import WeaknessDetector, SkillAnalyzer
from .features import FeatureExtractor, DataPreprocessor, FeatureSelector
from .features.pipeline import FeatureEngineeringPipeline

__all__ = [
    "MLConfig",
    "ml_config",
    "SkillCategory",
    "ModelManager",
    "DataValidator",
    "PerformanceMonitor",
    "BaseMLModel",
    "WeaknessDetector",
    "SkillAnalyzer",
    "FeatureExtractor",
    "DataPreprocessor",
    "FeatureSelector",
    "FeatureEngineeringPipeline"
]
