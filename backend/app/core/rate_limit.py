"""Simple in-memory rate limiting."""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request

from app.core.exceptions import RateLimitExceededError


class RateLimiter:
    """
    Simple in-memory rate limiter.

    Note: This is a basic implementation for development.
    In production, use Redis-based rate limiting for distributed systems.
    """

    def __init__(self, times: int, seconds: int):
        """
        Initialize rate limiter.

        Args:
            times: Number of requests allowed
            seconds: Time window in seconds
        """
        self.times = times
        self.seconds = seconds
        self.requests: Dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request) -> None:
        """
        Check rate limit for the request.

        Args:
            request: FastAPI request object

        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        # Use client IP as identifier
        # In production, you might want to use authenticated user ID instead
        identifier = request.client.host if request.client else "unknown"

        current_time = time.time()
        window_start = current_time - self.seconds

        # Get request timestamps for this identifier
        request_times = self.requests[identifier]

        # Remove timestamps outside the window
        request_times[:] = [t for t in request_times if t > window_start]

        # Check if limit is exceeded
        if len(request_times) >= self.times:
            # Calculate reset time
            oldest_request = request_times[0]
            reset_time = oldest_request + self.seconds

            raise RateLimitExceededError(
                detail=f"Rate limit exceeded. Try again in {int(reset_time - current_time)} seconds."
            )

        # Add current request
        request_times.append(current_time)

        # Set rate limit headers (optional, but good practice)
        # Note: These headers are informational and won't be set in FastAPI
        # unless we use a custom middleware. For now, we skip this.


# Create rate limiter instances for different endpoints
auth_rate_limit = RateLimiter(times=5, seconds=60)  # 5 requests per minute
chat_rate_limit = RateLimiter(times=10, seconds=60)  # 10 requests per minute
standard_rate_limit = RateLimiter(times=60, seconds=60)  # 60 requests per minute
