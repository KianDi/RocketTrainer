"""
Redis-based Rate Limiter for ML API endpoints.

Implements sliding window rate limiting with different tiers for free and premium users.
Provides accurate rate limiting, proper cleanup, and comprehensive monitoring.
"""

import time
import json
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from uuid import UUID
import redis
import structlog
from dataclasses import dataclass

from app.config import settings

logger = structlog.get_logger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information for a user and endpoint."""
    limit: int
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None


@dataclass
class RateLimitConfig:
    """Rate limit configuration for different user tiers and endpoints."""

    # Rate limits per hour for different user tiers
    FREE_TIER_LIMITS = {
        "analyze-weaknesses": 10,
        "recommend-training": 10,
        "model-status": 60  # More generous for monitoring
    }

    PREMIUM_TIER_LIMITS = {
        "analyze-weaknesses": 100,
        "recommend-training": 100,
        "model-status": 300  # More generous for monitoring
    }

    # Development mode limits (much higher for testing)
    DEV_TIER_LIMITS = {
        "analyze-weaknesses": 1000,
        "recommend-training": 1000,
        "model-status": 3000
    }

    # Default limits if endpoint not specified
    DEFAULT_FREE_LIMIT = 10
    DEFAULT_PREMIUM_LIMIT = 100
    DEFAULT_DEV_LIMIT = 1000

    # Time window in seconds (1 hour)
    WINDOW_SIZE = 3600

    # Redis key TTL (slightly longer than window for cleanup)
    KEY_TTL = 3900


class MLRateLimiter:
    """Redis-based sliding window rate limiter for ML API endpoints."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Optional Redis client. If None, creates new connection.
        """
        self.redis = redis_client or redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        self.config = RateLimitConfig()
        
        # Redis key prefix for rate limiting
        self.key_prefix = "rate_limit:ml:"
        
        logger.info("ML Rate Limiter initialized",
                   window_size=self.config.WINDOW_SIZE,
                   free_limits=self.config.FREE_TIER_LIMITS,
                   premium_limits=self.config.PREMIUM_TIER_LIMITS,
                   dev_limits=self.config.DEV_TIER_LIMITS,
                   debug_mode=settings.debug)
    
    def _get_rate_limit_key(self, user_id: str, endpoint: str) -> str:
        """Generate Redis key for rate limiting."""
        return f"{self.key_prefix}{user_id}:{endpoint}"
    
    def _get_user_limits(self, is_premium: bool, endpoint: str) -> int:
        """Get rate limit for user tier and endpoint."""
        # In debug mode, use much higher limits for development
        if settings.debug:
            return self.config.DEV_TIER_LIMITS.get(
                endpoint, self.config.DEFAULT_DEV_LIMIT
            )
        elif is_premium:
            return self.config.PREMIUM_TIER_LIMITS.get(
                endpoint, self.config.DEFAULT_PREMIUM_LIMIT
            )
        else:
            return self.config.FREE_TIER_LIMITS.get(
                endpoint, self.config.DEFAULT_FREE_LIMIT
            )
    
    def check_rate_limit(
        self, 
        user_id: str, 
        endpoint: str, 
        is_premium: bool = False
    ) -> Tuple[bool, RateLimitInfo]:
        """
        Check if request is within rate limit using sliding window.
        
        Args:
            user_id: User identifier
            endpoint: API endpoint name (e.g., 'analyze-weaknesses')
            is_premium: Whether user has premium tier
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = time.time()
        window_start = current_time - self.config.WINDOW_SIZE
        
        # Get rate limit for this user/endpoint combination
        limit = self._get_user_limits(is_premium, endpoint)
        key = self._get_rate_limit_key(user_id, endpoint)
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Remove expired entries (outside sliding window)
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Execute pipeline
            results = pipe.execute()
            current_count = results[1]
            
            # Calculate remaining requests
            remaining = max(0, limit - current_count)
            
            # Calculate reset time (when oldest request will expire)
            reset_time = int(current_time + self.config.WINDOW_SIZE)
            
            # Check if request is allowed
            if current_count >= limit:
                # Rate limit exceeded
                logger.warning("Rate limit exceeded",
                             user_id=user_id,
                             endpoint=endpoint,
                             is_premium=is_premium,
                             current_count=current_count,
                             limit=limit)
                
                # Calculate retry after (when next request slot becomes available)
                try:
                    oldest_request = self.redis.zrange(key, 0, 0, withscores=True)
                    if oldest_request:
                        oldest_time = oldest_request[0][1]
                        retry_after = int(oldest_time + self.config.WINDOW_SIZE - current_time)
                        retry_after = max(1, retry_after)  # At least 1 second
                    else:
                        retry_after = 60  # Default 1 minute
                except Exception:
                    retry_after = 60  # Fallback
                
                rate_limit_info = RateLimitInfo(
                    limit=limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
                
                return False, rate_limit_info
            
            # Request is allowed - record it
            pipe = self.redis.pipeline()
            
            # Add current request to sliding window
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set TTL on key for cleanup
            pipe.expire(key, self.config.KEY_TTL)
            
            # Execute pipeline
            pipe.execute()
            
            # Update remaining count after adding request
            remaining = max(0, remaining - 1)
            
            rate_limit_info = RateLimitInfo(
                limit=limit,
                remaining=remaining,
                reset_time=reset_time
            )
            
            logger.debug("Rate limit check passed",
                        user_id=user_id,
                        endpoint=endpoint,
                        is_premium=is_premium,
                        current_count=current_count + 1,
                        limit=limit,
                        remaining=remaining)
            
            return True, rate_limit_info
            
        except Exception as e:
            logger.error("Rate limit check failed",
                        user_id=user_id,
                        endpoint=endpoint,
                        error=str(e))
            
            # On Redis error, allow request but log the issue
            # This ensures service availability even if Redis is down
            fallback_info = RateLimitInfo(
                limit=limit,
                remaining=limit - 1,
                reset_time=int(current_time + self.config.WINDOW_SIZE)
            )
            
            return True, fallback_info
    
    def get_rate_limit_status(
        self, 
        user_id: str, 
        endpoint: str, 
        is_premium: bool = False
    ) -> RateLimitInfo:
        """
        Get current rate limit status without consuming a request.
        
        Args:
            user_id: User identifier
            endpoint: API endpoint name
            is_premium: Whether user has premium tier
            
        Returns:
            Current rate limit information
        """
        current_time = time.time()
        window_start = current_time - self.config.WINDOW_SIZE
        
        limit = self._get_user_limits(is_premium, endpoint)
        key = self._get_rate_limit_key(user_id, endpoint)
        
        try:
            # Clean up expired entries and count current requests
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            results = pipe.execute()
            
            current_count = results[1]
            remaining = max(0, limit - current_count)
            reset_time = int(current_time + self.config.WINDOW_SIZE)
            
            return RateLimitInfo(
                limit=limit,
                remaining=remaining,
                reset_time=reset_time
            )
            
        except Exception as e:
            logger.error("Failed to get rate limit status",
                        user_id=user_id,
                        endpoint=endpoint,
                        error=str(e))
            
            # Return fallback status
            return RateLimitInfo(
                limit=limit,
                remaining=limit,
                reset_time=int(current_time + self.config.WINDOW_SIZE)
            )
    
    def reset_rate_limit(self, user_id: str, endpoint: str) -> bool:
        """
        Reset rate limit for a user/endpoint (admin function).
        
        Args:
            user_id: User identifier
            endpoint: API endpoint name
            
        Returns:
            True if reset successful, False otherwise
        """
        key = self._get_rate_limit_key(user_id, endpoint)
        
        try:
            deleted = self.redis.delete(key)
            logger.info("Rate limit reset",
                       user_id=user_id,
                       endpoint=endpoint,
                       key_existed=bool(deleted))
            return True
            
        except Exception as e:
            logger.error("Failed to reset rate limit",
                        user_id=user_id,
                        endpoint=endpoint,
                        error=str(e))
            return False
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """
        Get overall rate limiting statistics.
        
        Returns:
            Dictionary with rate limiting statistics
        """
        try:
            # Get all rate limit keys
            pattern = f"{self.key_prefix}*"
            keys = self.redis.keys(pattern)
            
            stats = {
                "total_tracked_users": len(set(key.split(':')[2] for key in keys)),
                "total_rate_limit_keys": len(keys),
                "endpoints": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Analyze by endpoint
            endpoint_stats = {}
            for key in keys:
                parts = key.split(':')
                if len(parts) >= 4:
                    endpoint = parts[3]
                    if endpoint not in endpoint_stats:
                        endpoint_stats[endpoint] = 0
                    endpoint_stats[endpoint] += 1
            
            stats["endpoints"] = endpoint_stats
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get rate limit stats", error=str(e))
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def health_check(self) -> bool:
        """
        Perform health check on rate limiter.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Test basic Redis operations
            test_key = f"{self.key_prefix}health_check"
            test_score = time.time()
            
            # Test zadd and zcard operations
            self.redis.zadd(test_key, {str(test_score): test_score})
            count = self.redis.zcard(test_key)
            self.redis.delete(test_key)
            
            is_healthy = count == 1
            
            if is_healthy:
                logger.debug("Rate limiter health check passed")
            else:
                logger.error("Rate limiter health check failed",
                           expected_count=1, actual_count=count)
            
            return is_healthy
            
        except Exception as e:
            logger.error("Rate limiter health check failed", error=str(e))
            return False


# Global rate limiter instance
_rate_limiter: Optional[MLRateLimiter] = None


def get_rate_limiter() -> MLRateLimiter:
    """Get global rate limiter instance (singleton pattern)."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = MLRateLimiter()
    return _rate_limiter
