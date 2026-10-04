"""HTTP authentication and authorization middleware."""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.errors import ErrorCode, build_error_response
from app.core.exceptions import CrossOrganizationAccessError, InsufficientPermissionsError
from app.core.logger import get_logger, get_request_id
from app.core.observability import platform_metrics
from app.database.session import get_db_session
from app.infrastructure.iam.factory import build_iam_service

logger = get_logger(__name__)

_TENANT_PATH = re.compile(r"^/api/v1/tenants/(?P<tenant_id>[0-9a-f-]{36})")
_ORG_PATH = re.compile(r"^/api/v1/iam/organizations/(?P<org_id>[0-9a-f-]{36})")


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authenticate and authorize HTTP requests before route handlers."""

    PUBLIC_ROUTES: frozenset[tuple[str, str]] = frozenset(
        {
            ("POST", "/api/v1/iam/auth/login"),
            ("POST", "/api/v1/iam/auth/register"),
            ("POST", "/api/v1/iam/auth/refresh"),
            ("GET", "/api/v1/health"),
            ("GET", "/api/v1/health/"),
        }
    )

    PUBLIC_PREFIXES: tuple[str, ...] = (
        "/api/v1/health",
        "/api/v1/metrics",
        "/api/v1/integrations/oauth",
        "/api/v1/integrations/webhooks",
    )

    EXEMPT_PREFIXES: tuple[str, ...] = ("/twilio",)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/") or "/"
        method = request.method.upper()

        if self._is_public(method, path):
            return await call_next(request)

        if settings.DEBUG and path in ("/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return await call_next(request)

        if path == "/api/v1" and request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        if not path.startswith("/api/v1"):
            return await call_next(request)

        if not settings.database_enabled:
            body = build_error_response(
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message="Database is not configured. Set DATABASE_URL to enable enterprise APIs.",
                request_id=get_request_id(),
            )
            return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=body)

        try:
            principal = await self._authenticate_request(request)
        except Exception as exc:
            logger.info(
                "Authentication failed",
                extra_fields={"path": path, "error": str(exc)},
            )
            from app.core.exception_handlers import resolve_exception

            status_code, body = resolve_exception(exc)
            return JSONResponse(
                status_code=status_code,
                content=body,
                headers={"X-Request-ID": get_request_id() or ""},
            )

        request.state.principal = principal

        from app.core.rate_limit import check_authenticated_rate_limits

        allowed, retry_after, scope = check_authenticated_rate_limits(request, principal)
        if not allowed:
            platform_metrics.record_rate_limit()
            body = build_error_response(
                code=ErrorCode.RATE_LIMIT_EXCEEDED,
                message=f"Rate limit exceeded ({scope})",
                details={"scope": scope, "retry_after_seconds": retry_after},
                request_id=get_request_id(),
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=body,
                headers={
                    "Retry-After": str(retry_after or settings.RATE_LIMIT_WINDOW_SECONDS),
                    "X-Request-ID": get_request_id() or "",
                },
            )

        try:
            await self._authorize_request(request, principal)
        except Exception as exc:
            from app.core.exception_handlers import resolve_exception

            status_code, body = resolve_exception(exc)
            return JSONResponse(
                status_code=status_code,
                content=body,
                headers={"X-Request-ID": get_request_id() or ""},
            )

        return await call_next(request)

    def _is_public(self, method: str, path: str) -> bool:
        if (method, path) in self.PUBLIC_ROUTES:
            return True
        if (method, f"{path}/") in self.PUBLIC_ROUTES:
            return True
        return any(path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES)

    async def _authenticate_request(self, request: Request):
        auth_header = request.headers.get("Authorization", "")
        api_key = request.headers.get("X-Api-Key")

        async for session in get_db_session():
            auth = build_iam_service(session).build_authentication_service()
            if auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                return await auth.authenticate_bearer(token)
            if api_key and settings.IAM_ENABLE_API_KEY_AUTH:
                return await auth.authenticate_api_key(api_key.strip())
            break

        from app.core.exceptions import AuthenticationError

        raise AuthenticationError("Authentication required")

    async def _authorize_request(self, request: Request, principal) -> None:
        path = request.url.path.rstrip("/") or "/"

        tenant_match = _TENANT_PATH.match(path)
        if tenant_match:
            tenant_id = UUID(tenant_match.group("tenant_id"))
            async for session in get_db_session():
                auth = build_iam_service(session).build_authentication_service()
                await auth.validate_tenant_access(principal, tenant_id)
                break
            return

        org_match = _ORG_PATH.match(path)
        if org_match:
            org_id = UUID(org_match.group("org_id"))
            if principal.organization_id != org_id:
                raise CrossOrganizationAccessError("Cross-organization access denied")
            return

        if path == "/api/v1/tenants" and request.method.upper() in {"GET", "POST", "PATCH", "DELETE"}:
            if not principal.has_permission("manage_organization"):
                raise InsufficientPermissionsError(
                    "Missing permission: manage_organization",
                    permission="manage_organization",
                )
