"""Retry logic with exponential backoff for API calls."""

import os
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import requests

F = TypeVar("F", bound=Callable[..., Any])

DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 30.0
RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)


def get_max_retries() -> int:
    """Get max retries from env or default."""
    try:
        return int(os.environ.get("VIBE_MAX_RETRIES", DEFAULT_MAX_RETRIES))
    except ValueError:
        return DEFAULT_MAX_RETRIES


def with_retry(
    max_retries: int | None = None,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    retryable_statuses: tuple[int, ...] = RETRYABLE_STATUS_CODES,
) -> Callable[[F], F]:
    """Decorator for retrying API calls with exponential backoff + jitter.

    Args:
        max_retries: Maximum number of retry attempts (default from VIBE_MAX_RETRIES env or 3)
        base_delay: Base delay in seconds between retries
        max_delay: Maximum delay in seconds
        retryable_statuses: HTTP status codes that trigger a retry
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = max_retries if max_retries is not None else get_max_retries()
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except requests.HTTPError as e:
                    if e.response is not None and e.response.status_code not in retryable_statuses:
                        raise
                    if attempt == retries:
                        raise
                    delay = min(base_delay * (2**attempt) + random.uniform(0, 1), max_delay)
                    # Respect Retry-After header for 429s
                    if e.response is not None and e.response.status_code == 429:
                        retry_after = e.response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                delay = max(delay, float(retry_after))
                            except ValueError:
                                pass
                    time.sleep(delay)
                except requests.ConnectionError:
                    if attempt == retries:
                        raise
                    delay = min(base_delay * (2**attempt) + random.uniform(0, 1), max_delay)
                    time.sleep(delay)

        return wrapper  # type: ignore[return-value]

    return decorator
