"""Request timeout middleware."""

from __future__ import annotations

import asyncio
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.errors import ErrorCode, build_error_response
from app.core.logger import get_logger, get_request_id
from app.core.observability import platform_metrics

logger = get_logger(__name__)


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """Enforce configurable per-request timeout."""

    EXEMPT_PREFIXES = ("/api/v1/health", "/twilio")

    def _timeout_for_path(self, path: str) -> float:
        if "/knowledge" in path or "/rag" in path:
            return settings.REQUEST_TIMEOUT_KNOWLEDGE_SECONDS
        if "/planner" in path:
            return settings.REQUEST_TIMEOUT_PLANNER_SECONDS
        if "/verifier" in path:
            return settings.REQUEST_TIMEOUT_VERIFIER_SECONDS
        if "/tools" in path:
            return settings.REQUEST_TIMEOUT_TOOLS_SECONDS
        if "/workflow" in path:
            return settings.REQUEST_TIMEOUT_WORKFLOW_SECONDS
        return settings.REQUEST_TIMEOUT_DEFAULT_SECONDS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.REQUEST_TIMEOUT_ENABLED:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return await call_next(request)

        timeout = self._timeout_for_path(path)
        try:
            return await asyncio.wait_for(call_next(request), timeout=timeout)
        except asyncio.TimeoutError:
            platform_metrics.record_timeout()
            body = build_error_response(
                code=ErrorCode.REQUEST_TIMEOUT,
                message="Request timed out",
                details={"timeout_seconds": timeout, "path": path},
                request_id=get_request_id(),
            )
            logger.warning(
                "Request timeout",
                extra_fields={"path": path, "timeout_seconds": timeout},
            )
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content=body,
                headers={"X-Request-ID": get_request_id() or ""},
            )
