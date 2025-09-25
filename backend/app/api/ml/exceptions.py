"""
ML-specific exception classes for RocketTrainer.

Provides a comprehensive hierarchy of exceptions for ML operations
with proper error messages and HTTP status code mappings for API responses.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import structlog

logger = structlog.get_logger(__name__)


class MLModelError(Exception):
    """Base exception for ML model errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize ML model error.
        
        Args:
            message: Error message
            details: Optional additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "ML Model Error",
                "message": self.message,
                "details": self.details,
                "type": self.__class__.__name__
            }
        )


class InsufficientDataError(MLModelError):
    """Raised when there's insufficient data for ML analysis."""
    
    def __init__(self, message: str = "Insufficient data for analysis", 
                 required_matches: Optional[int] = None,
                 available_matches: Optional[int] = None):
        """
        Initialize insufficient data error.
        
        Args:
            message: Error message
            required_matches: Minimum required matches
            available_matches: Available matches count
        """
        details = {}
        if required_matches is not None:
            details["required_matches"] = required_matches
        if available_matches is not None:
            details["available_matches"] = available_matches
            
        super().__init__(message, details)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Insufficient Data",
                "message": self.message,
                "details": self.details,
                "type": self.__class__.__name__,
                "suggestion": "Upload more replay data or adjust analysis parameters"
            }
        )


class ModelNotTrainedError(MLModelError):
    """Raised when attempting to use an untrained model."""
    
    def __init__(self, model_name: str, message: Optional[str] = None):
        """
        Initialize model not trained error.
        
        Args:
            model_name: Name of the untrained model
            message: Optional custom message
        """
        default_message = f"Model '{model_name}' has not been trained yet"
        super().__init__(message or default_message, {"model_name": model_name})
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Model Not Available",
                "message": self.message,
                "details": self.details,
                "type": self.__class__.__name__,
                "suggestion": "Model is being trained. Please try again later."
            }
        )


class ModelPredictionError(MLModelError):
    """Raised when model prediction fails."""
    
    def __init__(self, model_name: str, message: str, 
                 prediction_input: Optional[Dict[str, Any]] = None):
        """
        Initialize model prediction error.
        
        Args:
            model_name: Name of the model that failed
            message: Error message
            prediction_input: Input that caused the error
        """
        details = {"model_name": model_name}
        if prediction_input:
            details["input_summary"] = str(prediction_input)[:200]  # Truncate for logging
            
        super().__init__(message, details)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Model Prediction Failed",
                "message": self.message,
                "details": self.details,
                "type": self.__class__.__name__,
                "suggestion": "Check input data format and try again"
            }
        )


class CacheError(MLModelError):
    """Raised when cache operations fail."""
    
    def __init__(self, operation: str, message: str, 
                 cache_key: Optional[str] = None):
        """
        Initialize cache error.
        
        Args:
            operation: Cache operation that failed (get, set, delete, etc.)
            message: Error message
            cache_key: Cache key involved in the operation
        """
        details = {"operation": operation}
        if cache_key:
            details["cache_key"] = cache_key
            
        super().__init__(message, details)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Cache Service Error",
                "message": self.message,
                "details": self.details,
                "type": self.__class__.__name__,
                "suggestion": "Cache service is temporarily unavailable. Request will proceed without caching."
            }
        )


class FeatureExtractionError(MLModelError):
    """Raised when feature extraction fails."""
    
    def __init__(self, message: str, feature_name: Optional[str] = None,
                 match_id: Optional[str] = None):
        """
        Initialize feature extraction error.
        
        Args:
            message: Error message
            feature_name: Name of the feature that failed extraction
            match_id: Match ID where extraction failed
        """
        details = {}
        if feature_name:
            details["feature_name"] = feature_name
        if match_id:
            details["match_id"] = match_id
            
        super().__init__(message, details)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Feature Extraction Failed",
                "message": self.message,
                "details": self.details,
                "type": self.__class__.__name__,
                "suggestion": "Check replay data quality and format"
            }
        )


class ModelLoadError(MLModelError):
    """Raised when model loading fails."""
    
    def __init__(self, model_name: str, model_path: Optional[str] = None,
                 original_error: Optional[str] = None):
        """
        Initialize model load error.
        
        Args:
            model_name: Name of the model that failed to load
            model_path: Path to the model file
            original_error: Original error message
        """
        message = f"Failed to load model '{model_name}'"
        details = {"model_name": model_name}
        
        if model_path:
            details["model_path"] = model_path
        if original_error:
            details["original_error"] = original_error
            
        super().__init__(message, details)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Model Loading Failed",
                "message": self.message,
                "details": self.details,
                "type": self.__class__.__name__,
                "suggestion": "Model service is temporarily unavailable. Please try again later."
            }
        )


class ValidationError(MLModelError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field_name: Optional[str] = None,
                 field_value: Optional[Any] = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field_name: Name of the field that failed validation
            field_value: Value that failed validation
        """
        details = {}
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            details["field_value"] = str(field_value)[:100]  # Truncate for logging
            
        super().__init__(message, details)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation Error",
                "message": self.message,
                "details": self.details,
                "type": self.__class__.__name__,
                "suggestion": "Check input parameters and format"
            }
        )


class RateLimitError(MLModelError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", 
                 limit: Optional[int] = None,
                 reset_time: Optional[int] = None):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            limit: Rate limit that was exceeded
            reset_time: Time when limit resets (seconds)
        """
        details = {}
        if limit:
            details["rate_limit"] = limit
        if reset_time:
            details["reset_in_seconds"] = reset_time
            
        super().__init__(message, details)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate Limit Exceeded",
                "message": self.message,
                "details": self.details,
                "type": self.__class__.__name__,
                "suggestion": "Please wait before making another request"
            }
        )


def log_ml_error(error: MLModelError, context: Optional[Dict[str, Any]] = None):
    """
    Log ML error with structured logging.
    
    Args:
        error: ML error to log
        context: Additional context for logging
    """
    log_context = {
        "error_type": error.__class__.__name__,
        "error_message": error.message,
        "error_details": error.details
    }
    
    if context:
        log_context.update(context)
    
    logger.error("ML operation failed", **log_context)


def handle_ml_exception(error: Exception, context: Optional[Dict[str, Any]] = None) -> HTTPException:
    """
    Handle any exception and convert to appropriate ML error.

    Args:
        error: Exception to handle
        context: Additional context

    Returns:
        HTTPException for FastAPI response
    """
    if isinstance(error, MLModelError):
        log_ml_error(error, context)
        return error.to_http_exception()

    # Pass through HTTPExceptions as-is (they're already properly formatted)
    if isinstance(error, HTTPException):
        # Log the HTTPException for monitoring
        log_context = context or {}
        log_context.update({
            "error_type": "HTTPException",
            "status_code": error.status_code,
            "detail": error.detail
        })
        logger.error("HTTP exception in ML operation", **log_context)
        return error

    # Convert generic exceptions to ML errors
    ml_error = MLModelError(
        message=f"Unexpected error: {str(error)}",
        details={"original_error": str(error), "error_type": error.__class__.__name__}
    )

    log_ml_error(ml_error, context)
    return ml_error.to_http_exception()
