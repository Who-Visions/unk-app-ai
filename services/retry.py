"""
Retry Utilities
===============
Retry decorators and utilities for resilient API calls.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable, Type, TypeVar
import logging

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log,
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retryable(
    attempts: int = 3,
    base_wait_seconds: float = 1.0,
    max_wait_seconds: float = 10.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Decorator for retryable functions with exponential backoff.
    
    Args:
        attempts: Maximum retry attempts
        base_wait_seconds: Base wait time (multiplier for exponential)
        max_wait_seconds: Maximum wait time cap
        exceptions: Tuple of exceptions to retry on
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retryable(attempts=3, base_wait_seconds=1.0)
        def fetch_data():
            return api.call()
    """
    if TENACITY_AVAILABLE:
        return retry(
            reraise=True,
            stop=stop_after_attempt(int(attempts)),
            wait=wait_exponential(
                multiplier=float(base_wait_seconds),
                max=float(max_wait_seconds)
            ),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
    else:
        # Fallback without tenacity
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                import time
                last_exception = None
                
                for attempt in range(attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < attempts - 1:
                            wait = min(
                                base_wait_seconds * (2 ** attempt),
                                max_wait_seconds
                            )
                            logger.warning(
                                f"Retry {attempt + 1}/{attempts} for {func.__name__} "
                                f"after {wait:.1f}s: {e}"
                            )
                            time.sleep(wait)
                
                raise last_exception  # type: ignore
            
            return wrapper
        return decorator


def retry_on_network_error(func: Callable[..., T]) -> Callable[..., T]:
    """
    Shorthand decorator for network-related retries.
    
    Uses sensible defaults for API calls.
    """
    return retryable(
        attempts=3,
        base_wait_seconds=1.0,
        max_wait_seconds=8.0,
        exceptions=(ConnectionError, TimeoutError, OSError),
    )(func)
