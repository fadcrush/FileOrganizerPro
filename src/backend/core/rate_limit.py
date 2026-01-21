"""
Phase 3 Week 4: Rate Limiting Implementation

Redis-backed sliding window rate limiting:
- Per-user limit: 100 requests/minute
- Global limit: 1000 requests/minute
- Per-endpoint limit: configurable

Usage:
    from src.backend.core.rate_limit import RateLimiter, rate_limit
    
    limiter = RateLimiter(redis=redis_client)
    
    # Check rate limit
    is_allowed = await limiter.is_allowed(user_id, "api_requests")
    
    # Or use dependency
    async def my_endpoint(rate_limit_check = Depends(rate_limit_dependency)):
        return {"status": "ok"}
"""

import redis.asyncio as redis
import time
from typing import Optional, Tuple
from datetime import datetime, timedelta
import logging
from fastapi import HTTPException, status, Request

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limiting configuration"""
    
    # Per-user limits (requests per minute)
    USER_API_LIMIT = 100  # General API requests
    USER_UPLOAD_LIMIT = 10  # File uploads
    USER_EXPORT_LIMIT = 5  # Report exports
    
    # Global limits (requests per minute)
    GLOBAL_API_LIMIT = 1000
    GLOBAL_UPLOAD_LIMIT = 100
    
    # Time windows (in seconds)
    WINDOW_SIZE = 60  # 1 minute
    
    # Response details
    RETRY_AFTER_HEADER = "Retry-After"
    RATE_LIMIT_HEADER = "X-RateLimit-Limit"
    RATE_LIMIT_REMAINING = "X-RateLimit-Remaining"
    RATE_LIMIT_RESET = "X-RateLimit-Reset"


class RateLimiter:
    """Redis-backed rate limiter using sliding window"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.config = RateLimitConfig()
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int = RateLimitConfig.WINDOW_SIZE,
    ) -> Tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            key: Rate limit key (e.g., "user_123", "global")
            limit: Max requests in window
            window: Time window in seconds
        
        Returns:
            (is_allowed, details) where details contains:
            - remaining: requests remaining
            - retry_after: seconds until reset
            - reset_time: unix timestamp when limit resets
        """
        try:
            now = time.time()
            window_start = now - window
            
            # Remove old requests outside window
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            request_count = await self.redis.zcard(key)
            
            # Calculate reset time (oldest request + window)
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            reset_time = (
                int(oldest[0][1]) + window
                if oldest
                else int(now) + window
            )
            remaining = max(0, limit - request_count)
            
            if request_count < limit:
                # Add current request
                await self.redis.zadd(key, {str(now): now})
                
                # Set expiry
                await self.redis.expire(key, window + 10)
                
                return True, {
                    "remaining": remaining - 1,
                    "retry_after": 0,
                    "reset_time": reset_time,
                    "limit": limit,
                }
            else:
                # Rate limit exceeded
                return False, {
                    "remaining": 0,
                    "retry_after": reset_time - int(now),
                    "reset_time": reset_time,
                    "limit": limit,
                }
        except Exception as e:
            logger.error(f"Rate limit error for {key}: {e}")
            # On error, allow request (fail open)
            return True, {"remaining": limit, "retry_after": 0, "reset_time": int(time.time()) + window, "limit": limit}
    
    async def check_user_limit(
        self,
        user_id: str,
        endpoint: str = "api",
    ) -> Tuple[bool, dict]:
        """Check user-specific rate limit"""
        key = f"ratelimit:user:{user_id}:{endpoint}"
        
        # Select limit based on endpoint
        if endpoint == "upload":
            limit = self.config.USER_UPLOAD_LIMIT
        elif endpoint == "export":
            limit = self.config.USER_EXPORT_LIMIT
        else:
            limit = self.config.USER_API_LIMIT
        
        return await self.is_allowed(key, limit)
    
    async def check_global_limit(
        self,
        endpoint: str = "api",
    ) -> Tuple[bool, dict]:
        """Check global rate limit"""
        key = f"ratelimit:global:{endpoint}"
        
        if endpoint == "upload":
            limit = self.config.GLOBAL_UPLOAD_LIMIT
        else:
            limit = self.config.GLOBAL_API_LIMIT
        
        return await self.is_allowed(key, limit)
    
    async def get_user_status(self, user_id: str) -> dict:
        """Get current rate limit status for user"""
        statuses = {}
        for endpoint in ["api", "upload", "export"]:
            is_allowed, details = await self.check_user_limit(user_id, endpoint)
            statuses[endpoint] = {
                "allowed": is_allowed,
                **details
            }
        return statuses
    
    async def reset_user_limit(self, user_id: str, endpoint: str = "api") -> bool:
        """Reset rate limit for user (admin only)"""
        try:
            key = f"ratelimit:user:{user_id}:{endpoint}"
            await self.redis.delete(key)
            logger.info(f"Reset rate limit for user {user_id} endpoint {endpoint}")
            return True
        except Exception as e:
            logger.error(f"Error resetting limit: {e}")
            return False
    
    async def reset_global_limit(self, endpoint: str = "api") -> bool:
        """Reset global rate limit (admin only)"""
        try:
            key = f"ratelimit:global:{endpoint}"
            await self.redis.delete(key)
            logger.info(f"Reset global rate limit for endpoint {endpoint}")
            return True
        except Exception as e:
            logger.error(f"Error resetting global limit: {e}")
            return False


class RateLimitException(HTTPException):
    """Rate limit exceeded exception"""
    
    def __init__(self, retry_after: int, limit_info: dict):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                "retry_after": retry_after,
                "limit": limit_info.get("limit"),
                "remaining": limit_info.get("remaining"),
                "reset_time": limit_info.get("reset_time"),
            }
        )
        self.headers = {
            "Retry-After": str(retry_after),
            RateLimitConfig.RATE_LIMIT_HEADER: str(limit_info.get("limit")),
            RateLimitConfig.RATE_LIMIT_REMAINING: str(limit_info.get("remaining")),
            RateLimitConfig.RATE_LIMIT_RESET: str(limit_info.get("reset_time")),
        }


async def apply_rate_limit(
    request: Request,
    user_id: Optional[str],
    limiter: RateLimiter,
    endpoint: str = "api",
) -> dict:
    """
    Apply rate limiting to a request.
    
    Args:
        request: FastAPI request
        user_id: Authenticated user ID
        limiter: RateLimiter instance
        endpoint: Endpoint type (api, upload, export)
    
    Returns:
        Rate limit details dict
    
    Raises:
        RateLimitException: If rate limit exceeded
    """
    # Check global limit
    global_allowed, global_details = await limiter.check_global_limit(endpoint)
    if not global_allowed:
        raise RateLimitException(
            global_details["retry_after"],
            global_details
        )
    
    # Check user limit if authenticated
    if user_id:
        user_allowed, user_details = await limiter.check_user_limit(user_id, endpoint)
        if not user_allowed:
            raise RateLimitException(
                user_details["retry_after"],
                user_details
            )
        return user_details
    
    return global_details


# Dependency injection helpers
async def rate_limit_dependency(
    request: Request,
    user_id: Optional[str] = None,
) -> dict:
    """FastAPI dependency for rate limiting"""
    from src.backend.core.cache import get_cache
    
    # Get limiter from app state or create new
    if hasattr(request.app, "rate_limiter"):
        limiter = request.app.rate_limiter
    else:
        cache = await get_cache()
        limiter = RateLimiter(cache.redis)
    
    # Determine endpoint from path
    endpoint = "api"
    if "/upload" in request.url.path:
        endpoint = "upload"
    elif "/export" in request.url.path:
        endpoint = "export"
    
    return await apply_rate_limit(request, user_id, limiter, endpoint)


class RateLimitMiddleware:
    """Middleware for automatic rate limiting"""
    
    def __init__(self, app, limiter: RateLimiter):
        self.app = app
        self.limiter = limiter
    
    async def __call__(self, request: Request, call_next):
        """Process request through rate limiter"""
        # Extract user ID from token or session
        user_id = self._extract_user_id(request)
        
        # Determine endpoint
        endpoint = "api"
        if "/upload" in request.url.path:
            endpoint = "upload"
        elif "/export" in request.url.path:
            endpoint = "export"
        
        try:
            limit_details = await apply_rate_limit(
                request,
                user_id,
                self.limiter,
                endpoint
            )
        except RateLimitException as e:
            return e
        
        # Call next middleware/handler
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers[RateLimitConfig.RATE_LIMIT_HEADER] = str(
            limit_details.get("limit")
        )
        response.headers[RateLimitConfig.RATE_LIMIT_REMAINING] = str(
            limit_details.get("remaining")
        )
        response.headers[RateLimitConfig.RATE_LIMIT_RESET] = str(
            limit_details.get("reset_time")
        )
        
        return response
    
    @staticmethod
    def _extract_user_id(request: Request) -> Optional[str]:
        """Extract user ID from request"""
        # Check Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # In real implementation, would decode JWT
            # For now, extract from custom header
            return request.headers.get("X-User-Id")
        return None
