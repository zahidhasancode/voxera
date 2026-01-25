"""Middleware for request context and logging."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import get_logger, set_call_id, set_request_id

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and propagate request_id and call_id."""

    REQUEST_ID_HEADER = "X-Request-ID"
    CALL_ID_HEADER = "X-Call-ID"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and inject context variables."""
        # Extract or generate request_id
        request_id = request.headers.get(self.REQUEST_ID_HEADER)
        if not request_id:
            request_id = str(uuid.uuid4())

        # Extract call_id if present
        call_id = request.headers.get(self.CALL_ID_HEADER)

        # Set context variables
        set_request_id(request_id)
        if call_id:
            set_call_id(call_id)

        # Track request start time
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.exception(
                "Request processing failed",
                extra_fields={
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": status_code,
                },
            )
            raise
        finally:
            # Calculate process time
            process_time = time.time() - start_time

            # Add request_id to response headers
            if hasattr(response, "headers"):
                response.headers[self.REQUEST_ID_HEADER] = request_id
                if call_id:
                    response.headers[self.CALL_ID_HEADER] = call_id

            # Log request
            logger.info(
                f"{request.method} {request.url.path}",
                extra_fields={
                    "method": request.method,
                    "path": str(request.url.path),
                    "query_params": dict(request.query_params) if request.query_params else {},
                    "status_code": status_code,
                    "client_ip": request.client.host if request.client else None,
                    "process_time": round(process_time, 4),
                },
            )

            # Log slow requests
            if process_time > 1.0:
                logger.warning(
                    "Slow request detected",
                    extra_fields={
                        "method": request.method,
                        "path": str(request.url.path),
                        "process_time": round(process_time, 4),
                    },
                )

        return response
