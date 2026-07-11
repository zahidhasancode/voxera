"""Middleware for request context, tracing, and observability."""

from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import ErrorCode, build_error_response
from app.core.logger import (
    clear_context,
    get_logger,
    get_request_id,
    set_call_id,
    set_correlation_id,
    set_endpoint,
    set_http_method,
    set_organization_id,
    set_request_id,
    set_tenant_id,
    set_user_id,
)
from app.core.observability import platform_metrics
from app.core.shutdown import shutdown_manager

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Propagate request/correlation IDs, user context, timing, and metrics."""

    REQUEST_ID_HEADER = "X-Request-ID"
    CORRELATION_ID_HEADER = "X-Correlation-ID"
    CALL_ID_HEADER = "X-Call-ID"
    PROCESS_TIME_HEADER = "X-Process-Time-Ms"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if shutdown_manager.is_shutting_down and request.url.path.startswith("/api/v1"):
            body = build_error_response(
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message="Server is shutting down",
            )
            return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=body)

        request_id = request.headers.get(self.REQUEST_ID_HEADER) or str(uuid.uuid4())
        correlation_id = request.headers.get(self.CORRELATION_ID_HEADER) or request_id
        call_id = request.headers.get(self.CALL_ID_HEADER)

        set_request_id(request_id)
        set_correlation_id(correlation_id)
        set_http_method(request.method)
        set_endpoint(request.url.path)
        if call_id:
            set_call_id(call_id)

        await shutdown_manager.begin_request()
        start_time = time.perf_counter()
        response: Response | None = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            logger.exception(
                "Request processing failed",
                extra_fields=self._log_fields(request, status_code, start_time),
            )
            raise
        finally:
            self._bind_principal_context(request)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            platform_metrics.record_request(latency_ms=latency_ms, status_code=status_code)

            if response is not None and hasattr(response, "headers"):
                response.headers[self.REQUEST_ID_HEADER] = request_id
                response.headers[self.CORRELATION_ID_HEADER] = correlation_id
                response.headers[self.PROCESS_TIME_HEADER] = str(latency_ms)
                if call_id:
                    response.headers[self.CALL_ID_HEADER] = call_id

            logger.info(
                f"{request.method} {request.url.path}",
                extra_fields={
                    **self._log_fields(request, status_code, start_time),
                    "latency_ms": latency_ms,
                },
            )

            if latency_ms > 1000:
                logger.warning(
                    "Slow request detected",
                    extra_fields={
                        "method": request.method,
                        "path": request.url.path,
                        "latency_ms": latency_ms,
                        "request_id": get_request_id(),
                    },
                )

            await shutdown_manager.end_request()
            clear_context()

    def _bind_principal_context(self, request: Request) -> None:
        principal = getattr(request.state, "principal", None)
        if principal is None:
            return
        if principal.user_id:
            set_user_id(str(principal.user_id))
        if principal.organization_id:
            set_organization_id(str(principal.organization_id))
        if principal.tenant_id:
            set_tenant_id(str(principal.tenant_id))

    def _log_fields(self, request: Request, status_code: int, start_time: float) -> dict:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params) if request.query_params else {},
            "status_code": status_code,
            "client_ip": request.client.host if request.client else None,
            "latency_ms": latency_ms,
            "request_id": get_request_id(),
        }
