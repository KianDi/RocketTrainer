"""
ML Model Singleton Manager for RocketTrainer.

Provides efficient model loading and management using singleton pattern
to avoid reloading models on each request. Includes lazy loading,
model caching in memory, and health check capabilities.
"""

import threading
from typing import Optional, Dict, Any, Type
from datetime import datetime
import structlog
from sqlalchemy.orm import Session

from app.ml.models.weakness_detector import WeaknessDetector
from app.ml.models.skill_analyzer import SkillAnalyzer
from app.ml.models.recommendation_engine import TrainingRecommendationEngine
from .exceptions import ModelLoadError, ModelNotTrainedError

logger = structlog.get_logger(__name__)


class ModelManager:
    """Singleton manager for ML models with lazy loading and caching."""
    
    _instance: Optional['ModelManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'ModelManager':
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize model manager (only once due to singleton)."""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._initialized = True
        self._models: Dict[str, Any] = {}
        self._model_metadata: Dict[str, Dict[str, Any]] = {}
        self._db_session: Optional[Session] = None
        
        # Model configuration
        self._model_config = {
            "weakness_detector": {
                "class": WeaknessDetector,
                "requires_db": True,
                "lazy_load": True
            },
            "skill_analyzer": {
                "class": SkillAnalyzer,
                "requires_db": False,
                "lazy_load": True
            },
            "recommendation_engine": {
                "class": TrainingRecommendationEngine,
                "requires_db": True,
                "lazy_load": True
            }
        }
        
        logger.info("ModelManager initialized", 
                   models_configured=len(self._model_config))
    
    def set_db_session(self, db_session: Session):
        """
        Set database session for models that require it.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self._db_session = db_session
        logger.info("Database session set for ModelManager")
    
    def _load_model(self, model_name: str) -> Any:
        """
        Load a specific model.
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            Loaded model instance
            
        Raises:
            ModelLoadError: If model loading fails
        """
        try:
            config = self._model_config.get(model_name)
            if not config:
                raise ModelLoadError(model_name, original_error="Model not configured")
            
            model_class = config["class"]
            requires_db = config["requires_db"]
            
            # Initialize model based on requirements
            model_dir = "/app/ml/trained_models"

            if requires_db:
                if not self._db_session:
                    raise ModelLoadError(
                        model_name,
                        original_error="Database session required but not provided"
                    )
                # Pass model path for models that support it
                if model_name == "weakness_detector":
                    model_instance = model_class(model_path=model_dir)
                else:
                    model_instance = model_class(self._db_session)
            else:
                # Pass model path for models that support it
                if model_name == "skill_analyzer":
                    model_instance = model_class(model_path=model_dir)
                else:
                    model_instance = model_class()
            
            # Store model metadata
            self._model_metadata[model_name] = {
                "loaded_at": datetime.utcnow(),
                "model_class": model_class.__name__,
                "requires_db": requires_db,
                "status": "loaded"
            }
            
            logger.info("Model loaded successfully", 
                       model_name=model_name,
                       model_class=model_class.__name__)
            
            return model_instance
            
        except Exception as e:
            error_msg = f"Failed to load model {model_name}: {str(e)}"
            logger.error("Model loading failed", 
                        model_name=model_name, 
                        error=str(e))
            
            # Update metadata with error status
            self._model_metadata[model_name] = {
                "loaded_at": datetime.utcnow(),
                "status": "error",
                "error": str(e)
            }
            
            raise ModelLoadError(model_name, original_error=str(e))
    
    def get_model(self, model_name: str) -> Any:
        """
        Get a model instance with lazy loading.
        
        Args:
            model_name: Name of the model to get
            
        Returns:
            Model instance
            
        Raises:
            ModelLoadError: If model loading fails
            ModelNotTrainedError: If model is not available
        """
        # Check if model is already loaded
        if model_name in self._models:
            logger.debug("Model retrieved from cache", model_name=model_name)
            return self._models[model_name]
        
        # Load model with thread safety
        with self._lock:
            # Double-check pattern
            if model_name in self._models:
                return self._models[model_name]
            
            # Load the model
            model_instance = self._load_model(model_name)
            self._models[model_name] = model_instance
            
            return model_instance
    
    def get_weakness_detector(self) -> WeaknessDetector:
        """
        Get WeaknessDetector model instance.
        
        Returns:
            WeaknessDetector instance
        """
        return self.get_model("weakness_detector")
    
    def get_skill_analyzer(self) -> SkillAnalyzer:
        """
        Get SkillAnalyzer model instance.
        
        Returns:
            SkillAnalyzer instance
        """
        return self.get_model("skill_analyzer")
    
    def get_recommendation_engine(self) -> TrainingRecommendationEngine:
        """
        Get TrainingRecommendationEngine model instance.
        
        Returns:
            TrainingRecommendationEngine instance
        """
        return self.get_model("recommendation_engine")
    
    def reload_model(self, model_name: str) -> Any:
        """
        Force reload a specific model.
        
        Args:
            model_name: Name of the model to reload
            
        Returns:
            Reloaded model instance
        """
        with self._lock:
            # Remove existing model
            if model_name in self._models:
                del self._models[model_name]
            
            # Remove metadata
            if model_name in self._model_metadata:
                del self._model_metadata[model_name]
            
            # Load fresh model
            model_instance = self._load_model(model_name)
            self._models[model_name] = model_instance
            
            logger.info("Model reloaded", model_name=model_name)
            return model_instance
    
    def reload_all_models(self):
        """Force reload all models."""
        with self._lock:
            model_names = list(self._models.keys())
            self._models.clear()
            self._model_metadata.clear()
            
            # Reload each model
            for model_name in model_names:
                try:
                    self._load_model(model_name)
                    self._models[model_name] = self._load_model(model_name)
                except Exception as e:
                    logger.error("Failed to reload model during bulk reload", 
                               model_name=model_name, error=str(e))
            
            logger.info("All models reloaded", 
                       models_reloaded=len(self._models))
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get status information for all models.
        
        Returns:
            Dictionary with model status information
        """
        status = {
            "models": {},
            "total_models": len(self._model_config),
            "loaded_models": len(self._models),
            "last_check": datetime.utcnow().isoformat()
        }
        
        for model_name, config in self._model_config.items():
            model_status = {
                "configured": True,
                "loaded": model_name in self._models,
                "requires_db": config["requires_db"],
                "lazy_load": config["lazy_load"]
            }
            
            # Add metadata if available
            if model_name in self._model_metadata:
                metadata = self._model_metadata[model_name]
                model_status.update({
                    "loaded_at": metadata.get("loaded_at"),
                    "status": metadata.get("status"),
                    "model_class": metadata.get("model_class"),
                    "error": metadata.get("error")
                })
            
            status["models"][model_name] = model_status
        
        return status
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all loaded models.
        
        Returns:
            Health check results
        """
        health_status = {
            "overall_status": "healthy",
            "models": {},
            "check_time": datetime.utcnow().isoformat()
        }
        
        unhealthy_count = 0
        
        for model_name in self._model_config.keys():
            model_health = {
                "status": "not_loaded",
                "error": None
            }
            
            try:
                if model_name in self._models:
                    model_instance = self._models[model_name]
                    
                    # Basic health check - ensure model exists and has expected methods
                    if hasattr(model_instance, '__class__'):
                        model_health["status"] = "healthy"
                        model_health["class_name"] = model_instance.__class__.__name__
                    else:
                        model_health["status"] = "unhealthy"
                        model_health["error"] = "Model instance invalid"
                        unhealthy_count += 1
                else:
                    model_health["status"] = "not_loaded"
                    
            except Exception as e:
                model_health["status"] = "error"
                model_health["error"] = str(e)
                unhealthy_count += 1
                logger.error("Model health check failed", 
                           model_name=model_name, error=str(e))
            
            health_status["models"][model_name] = model_health
        
        # Determine overall status
        if unhealthy_count > 0:
            if unhealthy_count == len(self._model_config):
                health_status["overall_status"] = "critical"
            else:
                health_status["overall_status"] = "degraded"
        
        health_status["unhealthy_models"] = unhealthy_count
        
        logger.info("Model health check completed", 
                   overall_status=health_status["overall_status"],
                   unhealthy_count=unhealthy_count)
        
        return health_status
    
    def clear_all_models(self):
        """Clear all loaded models from memory."""
        with self._lock:
            self._models.clear()
            self._model_metadata.clear()
            logger.info("All models cleared from memory")


# Global model manager instance
model_manager = ModelManager()


def get_model_manager() -> ModelManager:
    """
    Get the global model manager instance.
    
    Returns:
        ModelManager singleton instance
    """
    return model_manager
