"""
Base ML Model Class

Abstract base class for all machine learning models in RocketTrainer.
Provides common functionality for model training, prediction, and evaluation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
import structlog

from ..config import ml_config
from ..utils import model_manager, data_validator, performance_monitor

logger = structlog.get_logger(__name__)


class BaseMLModel(ABC):
    """Abstract base class for all ML models."""
    
    def __init__(self, model_name: str, model_version: str = "1.0.0"):
        self.model_name = model_name
        self.model_version = model_version
        self.model: Optional[BaseEstimator] = None
        self.is_trained = False
        self.feature_names: Optional[List[str]] = None
        self.training_metrics: Optional[Dict[str, Any]] = None
        
        logger.info("Initialized ML model", 
                   model_name=model_name, 
                   version=model_version)
    
    @abstractmethod
    def _create_model(self) -> BaseEstimator:
        """Create and return the underlying ML model instance."""
        pass
    
    @abstractmethod
    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features from raw data for model training/prediction."""
        pass
    
    @abstractmethod
    def _prepare_targets(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare target variables from raw data for model training."""
        pass
    
    def train(self, training_data: pd.DataFrame, validation_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Train the model on provided data."""
        try:
            logger.info("Starting model training", model_name=self.model_name)
            
            # Validate input data
            is_valid, errors = data_validator.validate_player_data(training_data)
            if not is_valid:
                raise ValueError(f"Invalid training data: {errors}")
            
            # Prepare features and targets
            X_train = self._prepare_features(training_data)
            y_train = self._prepare_targets(training_data)
            
            # Validate feature matrix
            is_valid, errors = data_validator.validate_feature_matrix(X_train, y_train)
            if not is_valid:
                raise ValueError(f"Invalid feature matrix: {errors}")
            
            # Create and train model
            if self.model is None:
                self.model = self._create_model()
            
            import time
            start_time = time.time()
            self.model.fit(X_train, y_train)
            training_time = time.time() - start_time
            
            # Evaluate on training data
            y_pred_train = self.model.predict(X_train)
            train_metrics = performance_monitor.log_model_performance(
                self.model_name, y_train, y_pred_train, training_time
            )
            
            # Evaluate on validation data if provided
            val_metrics = {}
            if validation_data is not None:
                X_val = self._prepare_features(validation_data)
                y_val = self._prepare_targets(validation_data)
                y_pred_val = self.model.predict(X_val)
                val_metrics = performance_monitor.log_model_performance(
                    f"{self.model_name}_validation", y_val, y_pred_val
                )
            
            # Store training results
            self.is_trained = True
            self.training_metrics = {
                "train": train_metrics,
                "validation": val_metrics,
                "training_samples": len(X_train),
                "feature_count": X_train.shape[1]
            }
            
            logger.info("Model training completed successfully", 
                       model_name=self.model_name,
                       training_time=training_time,
                       train_accuracy=train_metrics.get("accuracy"))
            
            return self.training_metrics
            
        except Exception as e:
            logger.error("Model training failed", 
                        model_name=self.model_name, 
                        error=str(e))
            raise
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Make predictions on new data."""
        if not self.is_trained or self.model is None:
            raise ValueError("Model must be trained before making predictions")
        
        try:
            # Prepare features
            X = self._prepare_features(data)
            
            # Validate features
            is_valid, errors = data_validator.validate_feature_matrix(X)
            if not is_valid:
                raise ValueError(f"Invalid feature matrix: {errors}")
            
            # Make predictions
            predictions = self.model.predict(X)
            
            logger.debug("Predictions made", 
                        model_name=self.model_name,
                        prediction_count=len(predictions))
            
            return predictions
            
        except Exception as e:
            logger.error("Prediction failed", 
                        model_name=self.model_name, 
                        error=str(e))
            raise
    
    def predict_proba(self, data: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities if supported by the model."""
        if not self.is_trained or self.model is None:
            raise ValueError("Model must be trained before making predictions")
        
        if not hasattr(self.model, 'predict_proba'):
            raise ValueError("Model does not support probability predictions")
        
        try:
            X = self._prepare_features(data)
            probabilities = self.model.predict_proba(X)
            
            logger.debug("Probability predictions made", 
                        model_name=self.model_name,
                        prediction_count=len(probabilities))
            
            return probabilities
            
        except Exception as e:
            logger.error("Probability prediction failed", 
                        model_name=self.model_name, 
                        error=str(e))
            raise
    
    def save(self, version: Optional[str] = None) -> str:
        """Save the trained model to disk."""
        if not self.is_trained or self.model is None:
            raise ValueError("Cannot save untrained model")
        
        version = version or self.model_version
        return model_manager.save_model(self.model, self.model_name, version)
    
    def load(self, version: Optional[str] = None) -> None:
        """Load a trained model from disk."""
        version = version or self.model_version
        self.model = model_manager.load_model(self.model_name, version)
        self.is_trained = True
        
        logger.info("Model loaded successfully", 
                   model_name=self.model_name, 
                   version=version)
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance if supported by the model."""
        if not self.is_trained or self.model is None:
            return None
        
        if not hasattr(self.model, 'feature_importances_'):
            return None
        
        if self.feature_names is None:
            return None
        
        importance_dict = dict(zip(self.feature_names, self.model.feature_importances_))
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information."""
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "is_trained": self.is_trained,
            "feature_count": len(self.feature_names) if self.feature_names else None,
            "training_metrics": self.training_metrics,
            "model_type": type(self.model).__name__ if self.model else None
        }
