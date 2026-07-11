"""IAM service facade."""

from uuid import UUID

from app.iam.schemas import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyRead,
    AuthTokens,
    LoginRequest,
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
    CurrentUserRead,
)


class IamService:
    def __init__(self, impl) -> None:
        self._impl = impl

    async def provision_organization(self, data: OrganizationCreate) -> OrganizationRead:
        return await self._impl.provision_organization(data)

    async def register_user(self, org_id: UUID, data: UserCreate, *, actor_id: UUID | None = None) -> UserRead:
        return await self._impl.register_user(org_id, data, actor_id=actor_id)

    async def invite_user(self, org_id: UUID, invite: UserInvite, *, actor_id: UUID) -> UserRead:
        return await self._impl.invite_user(org_id, invite, actor_id=actor_id)

    async def login(self, request: LoginRequest, *, ip: str | None = None, user_agent: str | None = None) -> AuthTokens:
        return await self._impl.login(request, ip=ip, user_agent=user_agent)

    async def register(self, body: RegisterRequest) -> AuthTokens:
        return await self._impl.register(body)

    async def refresh_tokens(self, body: RefreshRequest) -> AuthTokens:
        return await self._impl.refresh_tokens(body)

    async def logout(self, access_token: str, *, actor_id: UUID) -> SessionRead:
        return await self._impl.logout(access_token, actor_id=actor_id)

    async def get_current_user_profile(self, user_id: UUID, organization_id: UUID) -> CurrentUserRead:
        return await self._impl.get_current_user_profile(user_id, organization_id)

    def build_authentication_service(self):
        return self._impl.build_authentication_service()

    async def create_api_key(self, org_id: UUID, data: ApiKeyCreate, *, created_by: UUID) -> ApiKeyCreateResponse:
        return await self._impl.create_api_key(org_id, data, created_by=created_by)

    async def revoke_api_key(self, org_id: UUID, key_id: UUID, *, actor_id: UUID) -> ApiKeyRead:
        return await self._impl.revoke_api_key(org_id, key_id, actor_id=actor_id)

    async def list_users(self, org_id: UUID, *, actor_id: UUID) -> list[UserRead]:
        return await self._impl.list_users(org_id, actor_id=actor_id)

    async def list_sessions(self, user_id: UUID) -> list[SessionRead]:
        return await self._impl.list_sessions(user_id)

    async def revoke_session(self, session_id: UUID, *, actor_id: UUID) -> SessionRead:
        return await self._impl.revoke_session(session_id, actor_id=actor_id)

    async def get_security_policy(self, org_id: UUID) -> SecurityPolicyRead:
        return await self._impl.get_security_policy(org_id)

    async def update_security_policy(self, org_id: UUID, data: SecurityPolicyUpdate, *, actor_id: UUID) -> SecurityPolicyRead:
        return await self._impl.update_security_policy(org_id, data, actor_id=actor_id)

    async def list_permissions(self) -> list[PermissionRead]:
        return await self._impl.list_permissions()

    async def list_roles(self, org_id: UUID) -> list[RoleRead]:
        return await self._impl.list_roles(org_id)

    async def create_role(self, org_id: UUID, data: RoleCreate, *, actor_id: UUID) -> RoleRead:
        return await self._impl.create_role(org_id, data, actor_id=actor_id)

    async def list_audit_logs(self, org_id: UUID, *, actor_id: UUID, limit: int = 100) -> list[IamAuditRead]:
        return await self._impl.list_audit_logs(org_id, actor_id=actor_id, limit=limit)

    async def check_permission(self, org_id: UUID, user_id: UUID, permission: str) -> bool:
        return await self._impl.check_permission(org_id, user_id, permission)

    async def get_metrics(self, org_id: UUID) -> IamMetricsSnapshot:
        return await self._impl.get_metrics(org_id)

    async def get_organization(self, org_id: UUID) -> OrganizationRead:
        return await self._impl.get_organization(org_id)

    async def get_organization_by_tenant(self, tenant_id: UUID) -> OrganizationRead | None:
        return await self._impl.get_organization_by_tenant(tenant_id)

    async def list_api_keys(self, org_id: UUID) -> list[ApiKeyRead]:
        return await self._impl.list_api_keys(org_id)
