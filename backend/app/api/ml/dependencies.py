"""
FastAPI dependencies for ML API endpoints.

Provides rate limiting, user validation, and other middleware functionality
for ML API endpoints with proper error handling and monitoring.
"""

import json
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID
import structlog

from app.database import get_db
from app.models.user import User
from .rate_limiter import get_rate_limiter, RateLimitInfo
from .exceptions import handle_ml_exception

logger = structlog.get_logger(__name__)


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded."""
    
    def __init__(self, rate_limit_info: RateLimitInfo):
        self.rate_limit_info = rate_limit_info
        
        detail = {
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {rate_limit_info.limit} per hour",
            "limit": rate_limit_info.limit,
            "remaining": rate_limit_info.remaining,
            "reset_time": rate_limit_info.reset_time,
            "retry_after": rate_limit_info.retry_after
        }
        
        headers = {
            "X-RateLimit-Limit": str(rate_limit_info.limit),
            "X-RateLimit-Remaining": str(rate_limit_info.remaining),
            "X-RateLimit-Reset": str(rate_limit_info.reset_time),
        }
        
        if rate_limit_info.retry_after:
            headers["Retry-After"] = str(rate_limit_info.retry_after)
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers
        )


async def extract_user_id_from_request(request: Request) -> Optional[str]:
    """
    Extract user_id from request body for rate limiting.
    
    This function safely extracts user_id from the request body
    without consuming the request stream.
    """
    try:
        # Get the request body
        body = await request.body()
        
        if not body:
            return None
        
        # Parse JSON body
        try:
            body_data = json.loads(body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        
        # Extract user_id
        user_id = body_data.get('user_id')
        if user_id:
            # Validate UUID format
            try:
                UUID(user_id)
                return str(user_id)
            except (ValueError, TypeError):
                return None
        
        return None
        
    except Exception as e:
        logger.warning("Failed to extract user_id from request", error=str(e))
        return None


async def get_user_tier(user_id: str, db: Session) -> bool:
    """
    Get user tier (premium status) from database.
    
    Args:
        user_id: User identifier
        db: Database session
        
    Returns:
        True if user is premium, False if free tier
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user.is_premium
        else:
            # User not found - treat as free tier
            logger.warning("User not found for rate limiting", user_id=user_id)
            return False
            
    except Exception as e:
        logger.error("Failed to get user tier", user_id=user_id, error=str(e))
        # On error, treat as free tier (more restrictive)
        return False


def create_rate_limit_dependency(endpoint_name: str):
    """
    Create a rate limiting dependency for a specific endpoint.
    
    Args:
        endpoint_name: Name of the endpoint (e.g., 'analyze-weaknesses')
        
    Returns:
        FastAPI dependency function
    """
    
    async def rate_limit_dependency(
        request: Request,
        response: Response,
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """
        Rate limiting dependency for ML endpoints.
        
        Extracts user_id from request body, checks rate limits,
        and adds rate limit headers to response.
        """
        rate_limiter = get_rate_limiter()
        
        try:
            # Extract user_id from request body
            user_id = await extract_user_id_from_request(request)
            
            if not user_id:
                # No user_id found - this might be a malformed request
                # Let the endpoint handle validation, but don't rate limit
                logger.warning("No user_id found in request for rate limiting",
                             endpoint=endpoint_name,
                             path=request.url.path)
                
                # Return empty rate limit info
                return {
                    "rate_limit_applied": False,
                    "reason": "no_user_id"
                }
            
            # Get user tier (premium status)
            is_premium = await get_user_tier(user_id, db)
            
            # Check rate limit
            is_allowed, rate_limit_info = rate_limiter.check_rate_limit(
                user_id=user_id,
                endpoint=endpoint_name,
                is_premium=is_premium
            )
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(rate_limit_info.limit)
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_info.remaining)
            response.headers["X-RateLimit-Reset"] = str(rate_limit_info.reset_time)
            
            if not is_allowed:
                # Rate limit exceeded
                logger.warning("Rate limit exceeded for ML endpoint",
                             user_id=user_id,
                             endpoint=endpoint_name,
                             is_premium=is_premium,
                             limit=rate_limit_info.limit,
                             remaining=rate_limit_info.remaining)
                
                raise RateLimitExceeded(rate_limit_info)
            
            # Rate limit check passed
            logger.debug("Rate limit check passed",
                        user_id=user_id,
                        endpoint=endpoint_name,
                        is_premium=is_premium,
                        remaining=rate_limit_info.remaining)
            
            return {
                "rate_limit_applied": True,
                "user_id": user_id,
                "is_premium": is_premium,
                "rate_limit_info": rate_limit_info
            }
            
        except RateLimitExceeded:
            # Re-raise rate limit exceptions
            raise
        except Exception as e:
            # Log error but don't block request
            logger.error("Rate limiting error",
                        endpoint=endpoint_name,
                        error=str(e))
            
            # On error, allow request but log the issue
            return {
                "rate_limit_applied": False,
                "reason": "rate_limit_error",
                "error": str(e)
            }
    
    return rate_limit_dependency


# Create rate limiting dependencies for each ML endpoint
rate_limit_weakness_analysis = create_rate_limit_dependency("analyze-weaknesses")
rate_limit_training_recommendations = create_rate_limit_dependency("recommend-training")
rate_limit_model_status = create_rate_limit_dependency("model-status")


async def add_rate_limit_headers_middleware(request: Request, call_next):
    """
    Middleware to add rate limit headers to responses.
    
    This middleware checks if rate limit headers were set during
    request processing and adds them to the response.
    """
    response = await call_next(request)
    
    # Check if rate limit headers were set
    if hasattr(request.state, 'rate_limit_headers'):
        for header_name, header_value in request.state.rate_limit_headers.items():
            response.headers[header_name] = header_value
    
    return response


def get_rate_limit_status_for_user(
    user_id: str,
    endpoint: str,
    is_premium: bool = False
) -> RateLimitInfo:
    """
    Get rate limit status for a user without consuming a request.
    
    Utility function for checking rate limit status.
    """
    rate_limiter = get_rate_limiter()
    return rate_limiter.get_rate_limit_status(user_id, endpoint, is_premium)


def reset_rate_limit_for_user(user_id: str, endpoint: str) -> bool:
    """
    Reset rate limit for a user (admin function).
    
    Args:
        user_id: User identifier
        endpoint: Endpoint name
        
    Returns:
        True if reset successful
    """
    rate_limiter = get_rate_limiter()
    return rate_limiter.reset_rate_limit(user_id, endpoint)


def get_rate_limiting_stats() -> Dict[str, Any]:
    """
    Get overall rate limiting statistics.
    
    Returns:
        Dictionary with rate limiting statistics
    """
    rate_limiter = get_rate_limiter()
    return rate_limiter.get_rate_limit_stats()


def health_check_rate_limiter() -> bool:
    """
    Perform health check on rate limiter.
    
    Returns:
        True if healthy, False otherwise
    """
    rate_limiter = get_rate_limiter()
    return rate_limiter.health_check()
