"""
ML Models Package

Contains machine learning model implementations for RocketTrainer:
- WeaknessDetector: Identifies player weaknesses from gameplay data
- TrainingRecommender: Recommends training packs based on weaknesses
- BaseModel: Abstract base class for all ML models
"""

from .base import BaseMLModel
from .weakness_detector import WeaknessDetector
from .skill_analyzer import SkillAnalyzer

__all__ = [
    "BaseMLModel",
    "WeaknessDetector",
    "SkillAnalyzer"
]
