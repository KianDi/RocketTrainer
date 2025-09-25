"""
Feature Engineering Package

Contains feature extraction and data preprocessing components:
- FeatureExtractor: Extracts ML features from player statistics
- DataPreprocessor: Preprocesses data for ML models
- FeatureSelector: Selects optimal features for model training
"""

from .extractor import FeatureExtractor
from .preprocessor import DataPreprocessor, create_skill_category_features
from .selector import FeatureSelector
from .pipeline import FeatureEngineeringPipeline

__all__ = [
    "FeatureExtractor",
    "DataPreprocessor",
    "FeatureSelector",
    "FeatureEngineeringPipeline",
    "create_skill_category_features"
]
