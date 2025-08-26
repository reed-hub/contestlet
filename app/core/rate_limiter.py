import time
import asyncio
from typing import Dict, Optional, Union
from collections import defaultdict, deque
from functools import wraps
from app.core.config import get_settings
from app.core.exceptions import raise_rate_limit_error


class RateLimiter:
    """Elegant rate limiter with Redis and in-memory fallback"""
    
    def __init__(self):
        self._settings = get_settings()
        self._redis_client = None
        self._in_memory_limiter = InMemoryRateLimiter()
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis client if available"""
        try:
            import redis
            self._redis_client = redis.from_url(
                self._settings.redis_url,
                decode_responses=True
            )
            # Test connection
            self._redis_client.ping()
            print("🔴 Redis rate limiter initialized")
        except Exception as e:
            print(f"⚠️ Redis unavailable, using in-memory rate limiter: {e}")
            self._redis_client = None
    
    async def is_allowed_async(self, key: str, max_requests: Optional[int] = None, window_seconds: Optional[int] = None) -> bool:
        """Async rate limit check with Redis support"""
        if self._redis_client:
            return await self._redis_check(key, max_requests, window_seconds)
        return self._in_memory_check(key, max_requests, window_seconds)
    
    def is_allowed(self, key: str, max_requests: Optional[int] = None, window_seconds: Optional[int] = None) -> bool:
        """Sync rate limit check with Redis support"""
        if self._redis_client:
            return self._redis_check_sync(key, max_requests, window_seconds)
        return self._in_memory_check(key, max_requests, window_seconds)
    
    async def _redis_check(self, key: str, max_requests: Optional[int] = None, window_seconds: Optional[int] = None) -> bool:
        """Redis-based rate limit check"""
        max_req = max_requests or self._settings.rate_limit_requests
        window = window_seconds or self._settings.rate_limit_window
        
        current_time = int(time.time())
        window_start = current_time - window
        
        # Use Redis pipeline for atomic operations
        pipe = self._redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
        pipe.zcard(key)  # Count current entries
        pipe.zadd(key, {str(current_time): current_time})  # Add current request
        pipe.expire(key, window)  # Set expiration
        
        results = pipe.execute()
        current_count = results[1]
        
        return current_count < max_req
    
    def _redis_check_sync(self, key: str, max_requests: Optional[int] = None, window_seconds: Optional[int] = None) -> bool:
        """Sync Redis-based rate limit check"""
        max_req = max_requests or self._settings.rate_limit_requests
        window = window_seconds or self._settings.rate_limit_window
        
        current_time = int(time.time())
        window_start = current_time - window
        
        pipe = self._redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, window)
        
        results = pipe.execute()
        current_count = results[1]
        
        return current_count < max_req
    
    def _in_memory_check(self, key: str, max_requests: Optional[int] = None, window_seconds: Optional[int] = None) -> bool:
        """In-memory rate limit check"""
        return self._in_memory_limiter.is_allowed(key, max_requests, window_seconds)
    
    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for the key"""
        if self._redis_client:
            return self._redis_get_remaining(key)
        return self._in_memory_limiter.get_remaining_requests(key)
    
    def _redis_get_remaining(self, key: str) -> int:
        """Get remaining requests from Redis"""
        try:
            current_time = int(time.time())
            window_start = current_time - self._settings.rate_limit_window
            
            # Remove old entries and count current ones
            self._redis_client.zremrangebyscore(key, 0, window_start)
            current_count = self._redis_client.zcard(key)
            
            return max(0, self._settings.rate_limit_requests - current_count)
        except Exception:
            return self._settings.rate_limit_requests
    
    def get_reset_time(self, key: str) -> Optional[float]:
        """Get when the rate limit resets for the key"""
        if self._redis_client:
            return self._redis_get_reset_time(key)
        return self._in_memory_limiter.get_reset_time(key)
    
    def _redis_get_reset_time(self, key: str) -> Optional[float]:
        """Get reset time from Redis"""
        try:
            oldest_request = self._redis_client.zrange(key, 0, 0, withscores=True)
            if oldest_request:
                oldest_time = oldest_request[0][1]
                return oldest_time + self._settings.rate_limit_window
        except Exception:
            pass
        return None
    
    def reset_key(self, key: str) -> bool:
        """Reset rate limit for a specific key"""
        try:
            if self._redis_client:
                self._redis_client.delete(key)
            else:
                self._in_memory_limiter.reset_key(key)
            return True
        except Exception:
            return False


class InMemoryRateLimiter:
    """In-memory rate limiter with sliding window"""
    
    def __init__(self):
        self._settings = get_settings()
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, key: str, max_requests: Optional[int] = None, window_seconds: Optional[int] = None) -> bool:
        """Check if the request is allowed for the given key"""
        max_req = max_requests or self._settings.rate_limit_requests
        window = window_seconds or self._settings.rate_limit_window
        
        current_time = time.time()
        requests = self.requests[key]
        
        # Remove old requests outside the window
        while requests and requests[0] <= current_time - window:
            requests.popleft()
        
        # Check if we're under the limit
        if len(requests) < max_req:
            requests.append(current_time)
            return True
        
        return False
    
    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for the key"""
        current_time = time.time()
        requests = self.requests[key]
        
        # Remove old requests outside the window
        while requests and requests[0] <= current_time - self._settings.rate_limit_window:
            requests.popleft()
        
        return max(0, self._settings.rate_limit_requests - len(requests))
    
    def get_reset_time(self, key: str) -> Optional[float]:
        """Get when the rate limit resets for the key"""
        requests = self.requests[key]
        if not requests:
            return None
        
        return requests[0] + self._settings.rate_limit_window
    
    def reset_key(self, key: str) -> bool:
        """Reset rate limit for a specific key"""
        if key in self.requests:
            del self.requests[key]
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


# Decorator for rate limiting
def rate_limit(key_prefix: str, max_requests: Optional[int] = None, window_seconds: Optional[int] = None):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate rate limit key
            rate_key = f"{key_prefix}:{func.__name__}"
            
            if not await rate_limiter.is_allowed_async(rate_key, max_requests, window_seconds):
                remaining_time = rate_limiter.get_reset_time(rate_key)
                retry_after = int(remaining_time - time.time()) if remaining_time else 60
                raise_rate_limit_error(retry_after)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
