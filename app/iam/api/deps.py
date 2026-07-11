"""FastAPI authentication and authorization dependencies."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.dependencies import get_iam_service, map_domain_errors
from app.core.config import settings
from app.core.exceptions import InsufficientPermissionsError
from app.iam.auth.authentication_service import AuthenticationService
from app.iam.auth.principal import AuthenticatedPrincipal, TenantContext
from app.iam.services.iam_service import IamService

_bearer = HTTPBearer(auto_error=False)


def _principal_from_request(request: Request) -> AuthenticatedPrincipal | None:
    return getattr(request.state, "principal", None)


async def get_authentication_service(
    iam: IamService = Depends(get_iam_service),
) -> AuthenticationService:
    return iam.build_authentication_service()


async def get_current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    auth: AuthenticationService = Depends(get_authentication_service),
) -> AuthenticatedPrincipal:
    existing = _principal_from_request(request)
    if existing is not None:
        return existing

    if credentials and credentials.scheme.lower() == "bearer":
        try:
            principal = await auth.authenticate_bearer(credentials.credentials)
            request.state.principal = principal
            return principal
        except Exception as exc:
            raise map_domain_errors(exc) from exc

    api_key = request.headers.get("X-Api-Key")
    if api_key and settings.IAM_ENABLE_API_KEY_AUTH:
        try:
            principal = await auth.authenticate_api_key(api_key.strip())
            request.state.principal = principal
            return principal
        except Exception as exc:
            raise map_domain_errors(exc) from exc

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> AuthenticatedPrincipal:
    if principal.auth_method != "jwt" or principal.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User session required",
        )
    return principal


async def get_tenant_context(
    tenant_id: UUID,
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    auth: AuthenticationService = Depends(get_authentication_service),
) -> TenantContext:
    try:
        await auth.validate_tenant_access(principal, tenant_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc
    return TenantContext(
        tenant_id=tenant_id,
        organization_id=principal.organization_id,
        principal=principal,
        permissions=principal.permissions,
    )


def require_permissions(*permissions: str) -> Callable:
    """Dependency factory requiring all listed permissions."""

    async def _require(
        principal: AuthenticatedPrincipal = Depends(get_current_principal),
    ) -> AuthenticatedPrincipal:
        missing = [p for p in permissions if not principal.has_permission(p)]
        if missing:
            raise map_domain_errors(
                InsufficientPermissionsError(
                    f"Missing permissions: {', '.join(missing)}",
                    permission=missing[0],
                )
            )
        return principal

    return _require


def require_org_access(org_id: UUID) -> Callable:
    """Dependency factory validating organization path matches principal."""

    async def _require(
        principal: AuthenticatedPrincipal = Depends(get_current_principal),
        auth: AuthenticationService = Depends(get_authentication_service),
    ) -> AuthenticatedPrincipal:
        try:
            await auth.validate_organization_access(principal, org_id)
        except Exception as exc:
            raise map_domain_errors(exc) from exc
        return principal

    return _require


CurrentPrincipal = Annotated[AuthenticatedPrincipal, Depends(get_current_principal)]
CurrentUser = Annotated[AuthenticatedPrincipal, Depends(get_current_user)]
