import time
from typing import Dict, Optional
from collections import defaultdict, deque
from app.core.config import settings


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using sliding window.
    For production, use Redis-based rate limiting.
    """
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW

    def is_allowed(self, key: str) -> bool:
        """Check if the request is allowed for the given key"""
        current_time = time.time()
        requests = self.requests[key]
        
        # Remove old requests outside the window
        while requests and requests[0] <= current_time - self.window_seconds:
            requests.popleft()
        
        # Check if we're under the limit
        if len(requests) < self.max_requests:
            requests.append(current_time)
            return True
        
        return False

    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for the key"""
        current_time = time.time()
        requests = self.requests[key]
        
        # Remove old requests outside the window
        while requests and requests[0] <= current_time - self.window_seconds:
            requests.popleft()
        
        return max(0, self.max_requests - len(requests))

    def get_reset_time(self, key: str) -> Optional[float]:
        """Get when the rate limit resets for the key"""
        requests = self.requests[key]
        if not requests:
            return None
        
        return requests[0] + self.window_seconds


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()
