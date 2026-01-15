"""
Rate Limiter
============
Thread-safe rate limiter for API calls.
"""
from __future__ import annotations

import threading
import time


class RateLimiter:
    """
    Rate limiter with minimum interval between calls.
    
    Thread-safe implementation using monotonic clock.
    """
    
    def __init__(self, min_interval_seconds: float) -> None:
        """
        Initialize rate limiter.
        
        Args:
            min_interval_seconds: Minimum seconds between calls.
        """
        self._min_interval = max(0.0, float(min_interval_seconds))
        self._lock = threading.Lock()
        self._next_allowed = 0.0
    
    def wait(self) -> None:
        """Block until next call is allowed."""
        if self._min_interval <= 0:
            return
        
        with self._lock:
            now = time.monotonic()
            if now < self._next_allowed:
                sleep_time = self._next_allowed - now
                time.sleep(sleep_time)
            self._next_allowed = time.monotonic() + self._min_interval
    
    @property
    def min_interval(self) -> float:
        """Get minimum interval in seconds."""
        return self._min_interval


# Global rate limiters (initialized on first use)
_yfinance_limiter: RateLimiter | None = None
_gemini_limiter: RateLimiter | None = None


def get_yfinance_limiter(min_interval: float = 0.8) -> RateLimiter:
    """Get or create yfinance rate limiter."""
    global _yfinance_limiter
    if _yfinance_limiter is None:
        _yfinance_limiter = RateLimiter(min_interval)
    return _yfinance_limiter


def get_gemini_limiter(min_interval: float = 2.0) -> RateLimiter:
    """Get or create Gemini rate limiter."""
    global _gemini_limiter
    if _gemini_limiter is None:
        _gemini_limiter = RateLimiter(min_interval)
    return _gemini_limiter
