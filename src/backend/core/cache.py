"""
Phase 3 Week 4: Caching Layer Implementation

Redis-based caching for high-traffic endpoints:
- Category lists (TTL: 1 hour)
- User profiles (TTL: 30 minutes)
- Operation status (TTL: 5 minutes)
- Reports (TTL: 10 minutes)

Usage:
    from src.backend.core.cache import CacheManager, cache_key
    
    # Initialize
    cache = CacheManager(redis_url="redis://localhost:6379/0")
    
    # Cache a value
    await cache.set("key", value, ttl=3600)
    
    # Get from cache
    value = await cache.get("key")
    
    # Delete
    await cache.delete("key")
    
    # Or use decorators
    @cache.cached(ttl=3600)
    async def get_categories():
        return await db.get_categories()
"""

import json
import redis.asyncio as redis
import pickle
from typing import Any, Optional, Callable, Dict, List
from functools import wraps
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache manager"""
    
    # Default TTLs (in seconds)
    DEFAULT_TTL = 3600  # 1 hour
    CATEGORY_TTL = 3600  # 1 hour
    USER_PROFILE_TTL = 1800  # 30 minutes
    OPERATION_STATUS_TTL = 300  # 5 minutes
    REPORT_TTL = 600  # 10 minutes
    
    # Key prefixes
    KEY_PREFIX = "fileorg:"
    CATEGORY_PREFIX = "fileorg:category:"
    USER_PREFIX = "fileorg:user:"
    OPERATION_PREFIX = "fileorg:operation:"
    REPORT_PREFIX = "fileorg:report:"
    SEARCH_PREFIX = "fileorg:search:"
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize cache manager"""
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await redis.from_url(self.redis_url, decode_responses=False)
            await self.redis.ping()
            logger.info(f"✅ Connected to Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set cache value"""
        if not self.redis:
            return False
        
        try:
            if ttl is None:
                ttl = self.DEFAULT_TTL
            
            # Serialize value
            serialized = pickle.dumps(value)
            
            # Set with TTL
            await self.redis.setex(key, ttl, serialized)
            self.stats["sets"] += 1
            return True
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                self.stats["hits"] += 1
                return pickle.loads(value)
            else:
                self.stats["misses"] += 1
                return None
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete cache key"""
        if not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            self.stats["deletes"] += 1
            return True
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis:
            return 0
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                self.stats["deletes"] += len(keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Cache pattern delete error: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            return False
        
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for {key}: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cache keys"""
        if not self.redis:
            return False
        
        try:
            pattern = f"{self.KEY_PREFIX}*"
            count = await self.delete_pattern(pattern)
            logger.info(f"Cleared {count} cache keys")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            (self.stats["hits"] / total * 100)
            if total > 0
            else 0
        )
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"],
        }
    
    def cached(self, ttl: int = DEFAULT_TTL):
        """Decorator for caching async functions"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Call function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl=ttl)
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function and arguments"""
        # Convert args and kwargs to string
        arg_str = "_".join(str(arg) for arg in args if not callable(arg))
        kwarg_str = "_".join(f"{k}_{v}" for k, v in kwargs.items() if not callable(v))
        
        key_parts = [func_name, arg_str, kwarg_str]
        key = ":".join(part for part in key_parts if part)
        
        return f"cache:{key}"


# Specific cache key builders
def cache_key_categories() -> str:
    """Cache key for categories list"""
    return f"{CacheManager.CATEGORY_PREFIX}all"


def cache_key_user_profile(user_id: str) -> str:
    """Cache key for user profile"""
    return f"{CacheManager.USER_PREFIX}{user_id}"


def cache_key_operation_status(operation_id: str) -> str:
    """Cache key for operation status"""
    return f"{CacheManager.OPERATION_PREFIX}{operation_id}:status"


def cache_key_operation_files(operation_id: str, page: int = 1) -> str:
    """Cache key for operation files"""
    return f"{CacheManager.OPERATION_PREFIX}{operation_id}:files:page_{page}"


def cache_key_report(operation_id: str) -> str:
    """Cache key for operation report"""
    return f"{CacheManager.REPORT_PREFIX}{operation_id}"


def cache_key_duplicates(operation_id: str) -> str:
    """Cache key for duplicates"""
    return f"{CacheManager.OPERATION_PREFIX}{operation_id}:duplicates"


def cache_key_search(operation_id: str, query: str, page: int = 1) -> str:
    """Cache key for search results"""
    # Hash the query to avoid key length issues
    query_hash = hash(query) & 0x7fffffff
    return f"{CacheManager.SEARCH_PREFIX}{operation_id}:query_{query_hash}:page_{page}"


class CacheInvalidator:
    """Invalidate cache when data changes"""
    
    def __init__(self, cache: CacheManager):
        self.cache = cache
    
    async def invalidate_categories(self):
        """Invalidate categories cache"""
        await self.cache.delete(cache_key_categories())
    
    async def invalidate_user(self, user_id: str):
        """Invalidate user profile cache"""
        await self.cache.delete(cache_key_user_profile(user_id))
    
    async def invalidate_operation(self, operation_id: str):
        """Invalidate all operation-related caches"""
        pattern = f"{CacheManager.OPERATION_PREFIX}{operation_id}:*"
        await self.cache.delete_pattern(pattern)
        
        # Also invalidate report
        await self.cache.delete(cache_key_report(operation_id))
    
    async def invalidate_user_operations(self, user_id: str):
        """Invalidate all operation caches for a user"""
        # In a real implementation, would track user -> operations mapping
        # For now, clear operation prefix for the user
        pattern = f"{CacheManager.OPERATION_PREFIX}*"
        await self.cache.delete_pattern(pattern)
    
    async def invalidate_search(self, operation_id: str):
        """Invalidate search cache for operation"""
        pattern = f"{CacheManager.SEARCH_PREFIX}{operation_id}:*"
        await self.cache.delete_pattern(pattern)


# Global cache instance
_cache_instance: Optional[CacheManager] = None


async def get_cache() -> CacheManager:
    """Get or create global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager()
        await _cache_instance.connect()
    return _cache_instance


async def shutdown_cache():
    """Shutdown cache"""
    global _cache_instance
    if _cache_instance:
        await _cache_instance.disconnect()
        _cache_instance = None
