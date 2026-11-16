from collections import defaultdict, deque
import threading
import time
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding-window rate limiter for auth endpoints."""

    def __init__(self) -> None:
        self._hits: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def check(self, key: str, client_ip: str, max_requests: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        bucket_key = (key, client_ip)
        with self._lock:
            q = self._hits[bucket_key]
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many authentication attempts. Please wait a moment and try again.",
                )
            q.append(now)


auth_rate_limiter = SlidingWindowRateLimiter()


def rate_limit_auth(action: str, max_requests: int = 20, window_seconds: int = 60):
    def _dependency(request: Request) -> None:
        settings = get_settings()
        if settings.APP_ENV == "test":
            return
        client_host = request.client.host if request.client else "unknown"
        auth_rate_limiter.check(action, client_host, max_requests, window_seconds)

    return _dependency
