"""Rate limiting middleware — in-process sliding window."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.errors import ErrorCode, build_error_response
from app.core.logger import get_logger, get_request_id
from app.core.observability import platform_metrics
from fastapi.responses import JSONResponse

logger = get_logger(__name__)


class _SlidingWindowCounter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> tuple[bool, int | None]:
        now = time.monotonic()
        window = self._events[key]
        cutoff = now - self.window_seconds
        while window and window[0] <= cutoff:
            window.popleft()
        if len(window) >= self.limit:
            retry_after = max(1, int(self.window_seconds - (now - window[0])))
            return False, retry_after
        window.append(now)
        return True, None


# Module-level limiters for post-auth scopes (must persist across requests)
_auth_org_limiter = _SlidingWindowCounter(
    settings.RATE_LIMIT_PER_ORGANIZATION,
    settings.RATE_LIMIT_WINDOW_SECONDS,
)
_auth_tenant_limiter = _SlidingWindowCounter(
    settings.RATE_LIMIT_PER_ORGANIZATION,
    settings.RATE_LIMIT_WINDOW_SECONDS,
)
_auth_api_key_limiter = _SlidingWindowCounter(
    settings.RATE_LIMIT_PER_ORGANIZATION,
    settings.RATE_LIMIT_WINDOW_SECONDS,
)


def check_authenticated_rate_limits(request: Request, principal) -> tuple[bool, int | None, str | None]:
    """Post-auth rate limits for organization, tenant, and API key."""
    if not settings.RATE_LIMIT_ENABLED:
        return True, None, None

    checks: list[tuple[str, str, _SlidingWindowCounter]] = [
        ("organization", str(principal.organization_id), _auth_org_limiter),
    ]
    if principal.tenant_id:
        checks.append(("tenant", str(principal.tenant_id), _auth_tenant_limiter))
    api_key = request.headers.get("X-Api-Key")
    if api_key:
        checks.append(("api_key", api_key[:16], _auth_api_key_limiter))

    for scope, key, limiter in checks:
        allowed, retry_after = limiter.allow(f"{scope}:{key}")
        if not allowed:
            return False, retry_after, scope
    return True, None, None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP, API key, organization, tenant, and endpoint rate limits."""

    EXEMPT_PREFIXES = ("/api/v1/health", "/twilio", "/docs", "/redoc", "/openapi.json")

    def __init__(self, app) -> None:
        super().__init__(app)
        self._ip_limiter = _SlidingWindowCounter(
            settings.RATE_LIMIT_PER_IP,
            settings.RATE_LIMIT_WINDOW_SECONDS,
        )
        self._endpoint_limiter = _SlidingWindowCounter(
            settings.RATE_LIMIT_PER_ENDPOINT,
            settings.RATE_LIMIT_WINDOW_SECONDS,
        )
        self._org_limiter = _SlidingWindowCounter(
            settings.RATE_LIMIT_PER_ORGANIZATION,
            settings.RATE_LIMIT_WINDOW_SECONDS,
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        endpoint_key = f"{request.method}:{path}"

        checks = [
            ("ip", client_ip, self._ip_limiter),
            ("endpoint", endpoint_key, self._endpoint_limiter),
        ]

        for scope, key, limiter in checks:
            allowed, retry_after = limiter.allow(f"{scope}:{key}")
            if not allowed:
                platform_metrics.record_rate_limit()
                body = build_error_response(
                    code=ErrorCode.RATE_LIMIT_EXCEEDED,
                    message=f"Rate limit exceeded ({scope})",
                    details={"scope": scope, "retry_after_seconds": retry_after},
                    request_id=get_request_id(),
                )
                headers = {"Retry-After": str(retry_after or settings.RATE_LIMIT_WINDOW_SECONDS)}
                headers["X-Request-ID"] = get_request_id() or ""
                logger.warning(
                    "Rate limit exceeded",
                    extra_fields={"scope": scope, "key": key, "path": path},
                )
                return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=body, headers=headers)

        return await call_next(request)
