"""
ML Model Cache Manager for RocketTrainer.

Provides Redis-based caching for ML model predictions and analysis results
to achieve <500ms response time requirements. Includes cache invalidation
strategies and performance monitoring.
"""

import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis
import structlog
from uuid import UUID

from app.config import settings

logger = structlog.get_logger(__name__)


class MLModelCache:
    """Redis-based cache manager for ML model predictions and analysis."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize ML model cache.
        
        Args:
            redis_client: Optional Redis client. If None, creates new connection.
        """
        self.redis = redis_client or redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Cache TTL configurations (in seconds)
        self.ttl_config = {
            "weakness_analysis": 3600,      # 1 hour
            "training_recommendations": 1800, # 30 minutes
            "model_status": 300,            # 5 minutes
            "user_profile": 7200,           # 2 hours
        }
        
        # Cache key prefixes
        self.key_prefixes = {
            "weakness": "ml:weakness:",
            "training": "ml:training:",
            "status": "ml:status:",
            "profile": "ml:profile:",
            "stats": "ml:stats:"
        }
        
        logger.info("MLModelCache initialized",
                   redis_url=settings.redis_url)
    
    def _generate_cache_key(self, prefix: str, *args) -> str:
        """
        Generate a consistent cache key from arguments.
        
        Args:
            prefix: Cache key prefix
            *args: Arguments to include in key generation
            
        Returns:
            Generated cache key
        """
        # Convert all arguments to strings and create hash
        key_parts = [str(arg) for arg in args]
        key_string = ":".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{prefix}{key_hash}"
    
    def _serialize_data(self, data: Any) -> str:
        """
        Serialize data for Redis storage.
        
        Args:
            data: Data to serialize
            
        Returns:
            JSON string representation
        """
        def json_serializer(obj):
            """Custom JSON serializer for special types."""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, UUID):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(data, default=json_serializer, separators=(',', ':'))
    
    def _deserialize_data(self, data: str) -> Any:
        """
        Deserialize data from Redis storage.
        
        Args:
            data: JSON string to deserialize
            
        Returns:
            Deserialized data
        """
        return json.loads(data)
    
    def get_weakness_analysis(self, user_id: UUID, match_ids: Optional[List[UUID]] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached weakness analysis for a user.
        
        Args:
            user_id: User ID
            match_ids: Optional list of match IDs
            
        Returns:
            Cached analysis data or None if not found
        """
        try:
            cache_key = self._generate_cache_key(
                self.key_prefixes["weakness"],
                user_id,
                match_ids or "recent"
            )
            
            cached_data = self.redis.get(cache_key)
            if cached_data:
                logger.info("Cache hit for weakness analysis", 
                           user_id=str(user_id), cache_key=cache_key)
                return self._deserialize_data(cached_data)
            
            logger.info("Cache miss for weakness analysis", 
                       user_id=str(user_id), cache_key=cache_key)
            return None
            
        except Exception as e:
            logger.error("Error retrieving weakness analysis from cache", 
                        user_id=str(user_id), error=str(e))
            return None
    
    def cache_weakness_analysis(self, user_id: UUID, analysis: Dict[str, Any], 
                               match_ids: Optional[List[UUID]] = None) -> bool:
        """
        Cache weakness analysis results.
        
        Args:
            user_id: User ID
            analysis: Analysis results to cache
            match_ids: Optional list of match IDs
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(
                self.key_prefixes["weakness"],
                user_id,
                match_ids or "recent"
            )
            
            # Add cache metadata
            cache_data = {
                **analysis,
                "_cached_at": datetime.utcnow().isoformat(),
                "_cache_key": cache_key
            }
            
            serialized_data = self._serialize_data(cache_data)
            ttl = self.ttl_config["weakness_analysis"]
            
            success = self.redis.setex(cache_key, ttl, serialized_data)
            
            if success:
                logger.info("Cached weakness analysis", 
                           user_id=str(user_id), cache_key=cache_key, ttl=ttl)
            
            return bool(success)
            
        except Exception as e:
            logger.error("Error caching weakness analysis", 
                        user_id=str(user_id), error=str(e))
            return False
    
    def get_training_recommendations(self, user_id: UUID, skill_level: Optional[str] = None,
                                   categories: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached training recommendations for a user.
        
        Args:
            user_id: User ID
            skill_level: Optional skill level filter
            categories: Optional category filters
            
        Returns:
            Cached recommendations or None if not found
        """
        try:
            cache_key = self._generate_cache_key(
                self.key_prefixes["training"],
                user_id,
                skill_level or "auto",
                sorted(categories) if categories else "all"
            )
            
            cached_data = self.redis.get(cache_key)
            if cached_data:
                logger.info("Cache hit for training recommendations", 
                           user_id=str(user_id), cache_key=cache_key)
                return self._deserialize_data(cached_data)
            
            logger.info("Cache miss for training recommendations", 
                       user_id=str(user_id), cache_key=cache_key)
            return None
            
        except Exception as e:
            logger.error("Error retrieving training recommendations from cache", 
                        user_id=str(user_id), error=str(e))
            return None
    
    def cache_training_recommendations(self, user_id: UUID, recommendations: Dict[str, Any],
                                     skill_level: Optional[str] = None,
                                     categories: Optional[List[str]] = None) -> bool:
        """
        Cache training recommendations.
        
        Args:
            user_id: User ID
            recommendations: Recommendations to cache
            skill_level: Optional skill level filter
            categories: Optional category filters
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(
                self.key_prefixes["training"],
                user_id,
                skill_level or "auto",
                sorted(categories) if categories else "all"
            )
            
            # Add cache metadata
            cache_data = {
                **recommendations,
                "_cached_at": datetime.utcnow().isoformat(),
                "_cache_key": cache_key
            }
            
            serialized_data = self._serialize_data(cache_data)
            ttl = self.ttl_config["training_recommendations"]
            
            success = self.redis.setex(cache_key, ttl, serialized_data)
            
            if success:
                logger.info("Cached training recommendations", 
                           user_id=str(user_id), cache_key=cache_key, ttl=ttl)
            
            return bool(success)
            
        except Exception as e:
            logger.error("Error caching training recommendations", 
                        user_id=str(user_id), error=str(e))
            return False
    
    def get_model_status(self) -> Optional[Dict[str, Any]]:
        """
        Get cached model status information.
        
        Returns:
            Cached model status or None if not found
        """
        try:
            cache_key = f"{self.key_prefixes['status']}global"
            cached_data = self.redis.get(cache_key)
            
            if cached_data:
                logger.info("Cache hit for model status", cache_key=cache_key)
                return self._deserialize_data(cached_data)
            
            logger.info("Cache miss for model status", cache_key=cache_key)
            return None
            
        except Exception as e:
            logger.error("Error retrieving model status from cache", error=str(e))
            return None
    
    def cache_model_status(self, status: Dict[str, Any]) -> bool:
        """
        Cache model status information.
        
        Args:
            status: Model status to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            cache_key = f"{self.key_prefixes['status']}global"
            
            # Add cache metadata
            cache_data = {
                **status,
                "_cached_at": datetime.utcnow().isoformat(),
                "_cache_key": cache_key
            }
            
            serialized_data = self._serialize_data(cache_data)
            ttl = self.ttl_config["model_status"]
            
            success = self.redis.setex(cache_key, ttl, serialized_data)
            
            if success:
                logger.info("Cached model status", cache_key=cache_key, ttl=ttl)
            
            return bool(success)
            
        except Exception as e:
            logger.error("Error caching model status", error=str(e))
            return False
    
    def invalidate_user_cache(self, user_id: UUID) -> int:
        """
        Invalidate all cached data for a specific user.
        
        Args:
            user_id: User ID to invalidate cache for
            
        Returns:
            Number of keys deleted
        """
        try:
            # Find all keys for this user
            patterns = [
                f"{self.key_prefixes['weakness']}*{user_id}*",
                f"{self.key_prefixes['training']}*{user_id}*",
                f"{self.key_prefixes['profile']}*{user_id}*"
            ]
            
            deleted_count = 0
            for pattern in patterns:
                keys = self.redis.keys(pattern)
                if keys:
                    deleted_count += self.redis.delete(*keys)
            
            logger.info("Invalidated user cache", 
                       user_id=str(user_id), keys_deleted=deleted_count)
            
            return deleted_count
            
        except Exception as e:
            logger.error("Error invalidating user cache", 
                        user_id=str(user_id), error=str(e))
            return 0
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Cache statistics dictionary
        """
        try:
            # Get Redis info
            redis_info = self.redis.info()
            
            # Calculate cache statistics
            stats = {
                "total_keys": redis_info.get("db0", {}).get("keys", 0),
                "memory_usage_mb": redis_info.get("used_memory", 0) / (1024 * 1024),
                "hit_rate": 0.0,  # Would need to track this separately
                "connected_clients": redis_info.get("connected_clients", 0),
                "uptime_seconds": redis_info.get("uptime_in_seconds", 0),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error("Error getting cache statistics", error=str(e))
            return {
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    def health_check(self) -> bool:
        """
        Perform a health check on the cache system.
        
        Returns:
            True if cache is healthy, False otherwise
        """
        try:
            # Test basic Redis operations
            test_key = "ml:health_check"
            test_value = "ok"
            
            # Set and get test value
            self.redis.setex(test_key, 10, test_value)
            retrieved = self.redis.get(test_key)
            self.redis.delete(test_key)
            
            is_healthy = retrieved == test_value
            
            if is_healthy:
                logger.info("Cache health check passed")
            else:
                logger.error("Cache health check failed", 
                           expected=test_value, retrieved=retrieved)
            
            return is_healthy
            
        except Exception as e:
            logger.error("Cache health check failed with exception", error=str(e))
            return False
