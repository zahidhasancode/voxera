"""IAM REST API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.v1.dependencies import get_iam_service, map_domain_errors
from app.core.exceptions import CrossOrganizationAccessError, InsufficientPermissionsError
from app.iam.api.deps import CurrentUser, require_permissions
from app.iam.auth.principal import AuthenticatedPrincipal
from app.iam.schemas import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyRead,
    AuthTokens,
    CurrentUserRead,
    LoginRequest,
    MagicLinkRequest,
    OrganizationCreate,
    OrganizationRead,
    PermissionRead,
    RefreshRequest,
    RegisterRequest,
    RoleCreate,
    RoleRead,
    SecurityPolicyRead,
    SecurityPolicyUpdate,
    SessionRead,
    UserCreate,
    UserInvite,
    UserRead,
    IamAuditRead,
    IamMetricsSnapshot,
)
from app.iam.services.iam_service import IamService

auth_router = APIRouter()
org_router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@auth_router.post("/login", response_model=AuthTokens)
async def login(
    body: LoginRequest,
    request: Request,
    service: IamService = Depends(get_iam_service),
) -> AuthTokens:
    try:
        return await service.login(
            body,
            ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@auth_router.post("/register", response_model=AuthTokens, status_code=201)
async def register(
    body: RegisterRequest,
    service: IamService = Depends(get_iam_service),
) -> AuthTokens:
    try:
        return await service.register(body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@auth_router.post("/refresh", response_model=AuthTokens)
async def refresh_tokens(
    body: RefreshRequest,
    service: IamService = Depends(get_iam_service),
) -> AuthTokens:
    try:
        return await service.refresh_tokens(body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@auth_router.post("/logout", response_model=SessionRead)
async def logout(
    request: Request,
    current_user: CurrentUser,
    service: IamService = Depends(get_iam_service),
) -> SessionRead:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bearer token required")
    token = auth_header.split(" ", 1)[1].strip()
    try:
        return await service.logout(token, actor_id=current_user.user_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@auth_router.get("/me", response_model=CurrentUserRead)
async def get_me(
    current_user: CurrentUser,
    service: IamService = Depends(get_iam_service),
) -> CurrentUserRead:
    try:
        return await service.get_current_user_profile(
            current_user.user_id,
            current_user.organization_id,
        )
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@auth_router.post("/magic-link")
async def magic_link(body: MagicLinkRequest) -> dict:
    return {"status": "sent", "message": "Magic link provider not yet configured"}


@auth_router.get("/permissions", response_model=list[PermissionRead])
async def list_permissions(service: IamService = Depends(get_iam_service)) -> list[PermissionRead]:
    return await service.list_permissions()


@org_router.post("/organizations", response_model=OrganizationRead)
async def create_organization(
    body: OrganizationCreate,
    _: AuthenticatedPrincipal = Depends(require_permissions("manage_organization")),
    service: IamService = Depends(get_iam_service),
) -> OrganizationRead:
    try:
        return await service.provision_organization(body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@org_router.get("/organizations/{org_id}", response_model=OrganizationRead)
async def get_organization(
    org_id: UUID,
    current_user: CurrentUser,
    service: IamService = Depends(get_iam_service),
) -> OrganizationRead:
    if current_user.organization_id != org_id:
        raise map_domain_errors(CrossOrganizationAccessError("Cross-organization access denied"))
    try:
        return await service.get_organization(org_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@org_router.post("/organizations/{org_id}/users", response_model=UserRead)
async def register_user(
    org_id: UUID,
    body: UserCreate,
    current_user: AuthenticatedPrincipal = Depends(require_permissions("manage_users")),
    service: IamService = Depends(get_iam_service),
) -> UserRead:
    try:
        return await service.register_user(org_id, body, actor_id=current_user.user_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@org_router.post("/organizations/{org_id}/users/invite", response_model=UserRead)
async def invite_user(
    org_id: UUID,
    body: UserInvite,
    current_user: AuthenticatedPrincipal = Depends(require_permissions("manage_users")),
    service: IamService = Depends(get_iam_service),
) -> UserRead:
    try:
        return await service.invite_user(org_id, body, actor_id=current_user.user_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@org_router.get("/organizations/{org_id}/users", response_model=list[UserRead])
async def list_users(
    org_id: UUID,
    current_user: AuthenticatedPrincipal = Depends(require_permissions("manage_users")),
    service: IamService = Depends(get_iam_service),
) -> list[UserRead]:
    try:
        return await service.list_users(org_id, actor_id=current_user.user_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@org_router.get("/organizations/{org_id}/roles", response_model=list[RoleRead])
async def list_roles(
    org_id: UUID,
    current_user: CurrentUser,
    service: IamService = Depends(get_iam_service),
) -> list[RoleRead]:
    if current_user.organization_id != org_id:
        raise map_domain_errors(CrossOrganizationAccessError("Cross-organization access denied"))
    return await service.list_roles(org_id)


@org_router.post("/organizations/{org_id}/roles", response_model=RoleRead)
async def create_role(
    org_id: UUID,
    body: RoleCreate,
    current_user: AuthenticatedPrincipal = Depends(require_permissions("manage_roles")),
    service: IamService = Depends(get_iam_service),
) -> RoleRead:
    try:
        return await service.create_role(org_id, body, actor_id=current_user.user_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@org_router.post("/organizations/{org_id}/api-keys", response_model=ApiKeyCreateResponse)
async def create_api_key(
    org_id: UUID,
    body: ApiKeyCreate,
    current_user: AuthenticatedPrincipal = Depends(require_permissions("manage_api_keys")),
    service: IamService = Depends(get_iam_service),
) -> ApiKeyCreateResponse:
    try:
        return await service.create_api_key(org_id, body, created_by=current_user.user_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@org_router.get("/organizations/{org_id}/api-keys", response_model=list[ApiKeyRead])
async def list_api_keys(
    org_id: UUID,
    current_user: AuthenticatedPrincipal = Depends(require_permissions("manage_api_keys")),
    service: IamService = Depends(get_iam_service),
) -> list[ApiKeyRead]:
    return await service.list_api_keys(org_id)


@org_router.delete("/organizations/{org_id}/api-keys/{key_id}", response_model=ApiKeyRead)
async def revoke_api_key(
    org_id: UUID,
    key_id: UUID,
    current_user: AuthenticatedPrincipal = Depends(require_permissions("manage_api_keys")),
    service: IamService = Depends(get_iam_service),
) -> ApiKeyRead:
    try:
        return await service.revoke_api_key(org_id, key_id, actor_id=current_user.user_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@org_router.get("/organizations/{org_id}/security-policy", response_model=SecurityPolicyRead)
async def get_security_policy(
    org_id: UUID,
    current_user: AuthenticatedPrincipal = Depends(require_permissions("manage_security")),
    service: IamService = Depends(get_iam_service),
) -> SecurityPolicyRead:
    return await service.get_security_policy(org_id)


@org_router.patch("/organizations/{org_id}/security-policy", response_model=SecurityPolicyRead)
async def update_security_policy(
    org_id: UUID,
    body: SecurityPolicyUpdate,
    current_user: AuthenticatedPrincipal = Depends(require_permissions("manage_security")),
    service: IamService = Depends(get_iam_service),
) -> SecurityPolicyRead:
    try:
        return await service.update_security_policy(org_id, body, actor_id=current_user.user_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@org_router.get("/organizations/{org_id}/audit-logs", response_model=list[IamAuditRead])
async def list_iam_audit_logs(
    org_id: UUID,
    current_user: AuthenticatedPrincipal = Depends(require_permissions("view_audit_logs")),
    service: IamService = Depends(get_iam_service),
) -> list[IamAuditRead]:
    try:
        return await service.list_audit_logs(org_id, actor_id=current_user.user_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@org_router.get("/organizations/{org_id}/metrics", response_model=IamMetricsSnapshot)
async def get_iam_metrics(
    org_id: UUID,
    current_user: AuthenticatedPrincipal = Depends(require_permissions("view_analytics")),
    service: IamService = Depends(get_iam_service),
) -> IamMetricsSnapshot:
    return await service.get_metrics(org_id)


@org_router.get("/users/{user_id}/sessions", response_model=list[SessionRead])
async def list_sessions(
    user_id: UUID,
    current_user: CurrentUser,
    service: IamService = Depends(get_iam_service),
) -> list[SessionRead]:
    if current_user.user_id != user_id and not current_user.has_permission("manage_users"):
        raise map_domain_errors(
            InsufficientPermissionsError("Cannot list sessions for another user", permission="manage_users")
        )
    return await service.list_sessions(user_id)


@org_router.delete("/sessions/{session_id}", response_model=SessionRead)
async def revoke_session(
    session_id: UUID,
    current_user: CurrentUser,
    service: IamService = Depends(get_iam_service),
) -> SessionRead:
    try:
        return await service.revoke_session(session_id, actor_id=current_user.user_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc
