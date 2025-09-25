"""
ML Utility Functions and Helpers

Common utilities for machine learning operations including model management,
data validation, and performance monitoring.
"""

import os
import pickle
import logging
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import structlog

from .config import MLConfig, ml_config

logger = structlog.get_logger(__name__)


class ModelManager:
    """Manages ML model persistence, loading, and versioning."""
    
    def __init__(self, models_dir: str = "backend/ml/models/saved"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
    def save_model(self, model: BaseEstimator, model_name: str, version: str = "latest") -> str:
        """Save a trained model to disk."""
        try:
            model_path = self.models_dir / f"{model_name}_{version}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            logger.info("Model saved successfully", 
                       model_name=model_name, 
                       version=version, 
                       path=str(model_path))
            return str(model_path)
            
        except Exception as e:
            logger.error("Failed to save model", 
                        model_name=model_name, 
                        error=str(e))
            raise
    
    def load_model(self, model_name: str, version: str = "latest") -> BaseEstimator:
        """Load a trained model from disk."""
        try:
            model_path = self.models_dir / f"{model_name}_{version}.pkl"
            
            if not model_path.exists():
                raise FileNotFoundError(f"Model not found: {model_path}")
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            logger.info("Model loaded successfully", 
                       model_name=model_name, 
                       version=version)
            return model
            
        except Exception as e:
            logger.error("Failed to load model", 
                        model_name=model_name, 
                        error=str(e))
            raise
    
    def list_models(self) -> List[Dict[str, str]]:
        """List all available models."""
        models = []
        for model_file in self.models_dir.glob("*.pkl"):
            name_version = model_file.stem
            if "_" in name_version:
                name, version = name_version.rsplit("_", 1)
            else:
                name, version = name_version, "unknown"
            
            models.append({
                "name": name,
                "version": version,
                "path": str(model_file),
                "size": model_file.stat().st_size
            })
        
        return models


class DataValidator:
    """Validates data quality and consistency for ML operations."""
    
    @staticmethod
    def validate_player_data(data: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate player statistics data."""
        errors = []
        
        # Check required columns
        required_columns = ['goals', 'assists', 'saves', 'shots', 'score', 'boost_usage']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        # Check for negative values where they shouldn't exist
        numeric_columns = ['goals', 'assists', 'saves', 'shots', 'score']
        for col in numeric_columns:
            if col in data.columns and (data[col] < 0).any():
                errors.append(f"Negative values found in {col}")
        
        # Check for reasonable value ranges
        if 'score' in data.columns and (data['score'] > 2000).any():
            errors.append("Unreasonably high scores detected (>2000)")
        
        # Check for missing values in critical columns
        for col in required_columns:
            if col in data.columns and data[col].isnull().any():
                errors.append(f"Missing values found in {col}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def validate_feature_matrix(X: np.ndarray, y: Optional[np.ndarray] = None) -> Tuple[bool, List[str]]:
        """Validate feature matrix for ML training."""
        errors = []
        
        # Check for NaN or infinite values
        if np.isnan(X).any():
            errors.append("NaN values found in feature matrix")
        
        if np.isinf(X).any():
            errors.append("Infinite values found in feature matrix")
        
        # Check feature matrix shape
        if X.shape[0] == 0:
            errors.append("Empty feature matrix")
        
        if X.shape[1] == 0:
            errors.append("No features in feature matrix")
        
        # Validate target vector if provided
        if y is not None:
            if len(y) != X.shape[0]:
                errors.append("Feature matrix and target vector length mismatch")
            
            if np.isnan(y).any():
                errors.append("NaN values found in target vector")
        
        is_valid = len(errors) == 0
        return is_valid, errors


class PerformanceMonitor:
    """Monitors ML model performance and logs metrics."""
    
    @staticmethod
    def log_model_performance(
        model_name: str,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        training_time: float = None
    ) -> Dict[str, Any]:
        """Log comprehensive model performance metrics."""
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        report = classification_report(y_true, y_pred, output_dict=True)
        
        metrics = {
            "model_name": model_name,
            "accuracy": accuracy,
            "precision": report['weighted avg']['precision'],
            "recall": report['weighted avg']['recall'],
            "f1_score": report['weighted avg']['f1-score'],
            "training_time": training_time,
            "sample_count": len(y_true)
        }
        
        # Log metrics
        logger.info("Model performance metrics", **metrics)
        
        # Check if performance meets requirements
        if accuracy < ml_config.min_accuracy_threshold:
            logger.warning("Model accuracy below threshold", 
                          accuracy=accuracy, 
                          threshold=ml_config.min_accuracy_threshold)
        
        return metrics
    
    @staticmethod
    def log_prediction_confidence(predictions: np.ndarray, confidences: np.ndarray) -> Dict[str, float]:
        """Log prediction confidence statistics."""
        
        confidence_stats = {
            "mean_confidence": float(np.mean(confidences)),
            "min_confidence": float(np.min(confidences)),
            "max_confidence": float(np.max(confidences)),
            "std_confidence": float(np.std(confidences)),
            "low_confidence_count": int(np.sum(confidences < ml_config.confidence_threshold))
        }
        
        logger.info("Prediction confidence statistics", **confidence_stats)
        return confidence_stats


# Global instances
model_manager = ModelManager()
data_validator = DataValidator()
performance_monitor = PerformanceMonitor()
