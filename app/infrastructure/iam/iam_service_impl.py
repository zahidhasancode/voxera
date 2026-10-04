"""IAM service implementation."""

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.enums import SecurityEventSeverity, SecurityEventType, SystemRole, IamSessionStatus, IamUserStatus
from app.core.exceptions import (
    InsufficientPermissionsError,
    InvalidCredentialsError,
    IamUserNotFoundError,
    OrganizationNotFoundError,
    ApiKeyNotFoundError,
    IamSessionNotFoundError,
    TokenExpiredError,
    AuthenticationError,
)
from app.iam.api_keys.key_crypto import generate_api_key, verify_api_key
from app.iam.audit.audit_service import IamAuditService
from app.iam.auth.password import hash_password, verify_password
from app.iam.auth.token_service import TokenService
from app.iam.authorization.rbac_engine import RbacEngine
from app.iam.metrics.collector import IamMetricsCollector
from app.iam.permissions.catalog import PERMISSION_CATALOG
from app.iam.policies.security_policy_engine import SecurityPolicyEngine
from app.iam.schemas import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyRead,
    AuthTokens,
    IamAuditRead,
    LoginRequest,
    OrganizationCreate,
    OrganizationRead,
    PermissionRead,
    RefreshRequest,
    RegisterRequest,
    RoleCreate,
    RoleRead,
    SecurityEventRead,
    SecurityPolicyRead,
    SecurityPolicyUpdate,
    SessionRead,
    UserCreate,
    UserInvite,
    UserRead,
    IamMetricsSnapshot,
    CurrentUserRead,
)
from app.iam.validators.access_validator import IamAccessValidator
from app.iam.auth.authentication_service import AuthenticationService


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class IamServiceImpl:
    def __init__(
        self,
        *,
        organizations,
        users,
        memberships,
        roles,
        api_keys,
        sessions,
        policies,
        audit: IamAuditService,
        security_events,
        rbac: RbacEngine | None = None,
        tokens: TokenService | None = None,
        policy_engine: SecurityPolicyEngine | None = None,
        access: IamAccessValidator | None = None,
        metrics: IamMetricsCollector | None = None,
    ) -> None:
        self._orgs = organizations
        self._users = users
        self._memberships = memberships
        self._roles = roles
        self._api_keys = api_keys
        self._sessions = sessions
        self._policies = policies
        self._audit = audit
        self._security_events = security_events
        self._rbac = rbac or RbacEngine()
        self._tokens = tokens or TokenService()
        self._policy = policy_engine or SecurityPolicyEngine()
        self._access = access or IamAccessValidator()
        self._metrics = metrics or IamMetricsCollector()

    async def provision_organization(self, data: OrganizationCreate) -> OrganizationRead:
        org = await self._orgs.create(data)
        await self._policies.get_or_create(org.id)
        await self._audit.log(
            organization_id=org.id,
            action="organization.created",
            resource_type="organization",
            resource_id=str(org.id),
        )
        return org

    async def register_user(self, org_id: UUID, data: UserCreate, *, actor_id: UUID | None = None) -> UserRead:
        org = await self._orgs.get_by_id(org_id)
        if not org:
            raise OrganizationNotFoundError(f"Organization {org_id} not found")
        policy = await self._policies.get_or_create(org_id)
        self._policy.validate_password(policy, data.password)
        self._policy.validate_email_domain(policy, data.email)
        user = await self._users.create(data, hash_password(data.password))
        invite = UserInvite(email=data.email, role_slug=data.role_slug, department=data.department, title=data.title)
        member = await self._memberships.add(org_id, user.id, invite)
        await self._audit.log(
            organization_id=org_id,
            action="user.created",
            resource_type="user",
            resource_id=str(user.id),
            actor_user_id=actor_id,
        )
        return member

    async def invite_user(self, org_id: UUID, invite: UserInvite, *, actor_id: UUID) -> UserRead:
        await self._require_permission(org_id, actor_id, "manage_users")
        existing = await self._users.get_by_email(invite.email)
        if existing:
            user_read, _ = existing
            return await self._memberships.add(org_id, user_read.id, invite)
        temp_password = str(uuid4())
        user = await self._users.create(
            UserCreate(
                email=invite.email,
                name=invite.email.split("@")[0],
                password=temp_password,
                role_slug=invite.role_slug,
                department=invite.department,
                title=invite.title,
            ),
            hash_password(temp_password),
        )
        member = await self._memberships.add(org_id, user.id, invite)
        await self._audit.log(
            organization_id=org_id,
            action="user.invited",
            resource_type="user",
            resource_id=str(user.id),
            actor_user_id=actor_id,
            payload={"email": invite.email, "role": invite.role_slug},
        )
        return member

    async def login(self, request: LoginRequest, *, ip: str | None = None, user_agent: str | None = None) -> AuthTokens:
        creds = await self._users.get_by_email(request.email)
        if not creds or not creds[1] or not verify_password(request.password, creds[1]):
            self._metrics.record_login(success=False)
            await self._record_event(None, None, SecurityEventType.LOGIN_FAILURE, ip=ip)
            raise InvalidCredentialsError("Invalid email or password")
        user, _ = creds
        org_id = request.organization_id
        membership = None
        if org_id:
            membership = await self._memberships.get_membership(org_id, user.id)
            if not membership:
                raise InvalidCredentialsError("User is not a member of this organization")
        await self._users.update_last_login(user.id)
        role_slug = membership.role_slug if membership else SystemRole.VIEWER
        org = org_id or (await self._resolve_default_org(user.id))
        permissions = list(self._rbac.resolve_permissions(role_slug))
        session_id = uuid4()
        access = self._tokens.create_access_token(
            user_id=user.id, organization_id=org, role_slug=role_slug, permissions=permissions
        )
        refresh = self._tokens.create_refresh_token(user_id=user.id, session_id=session_id)
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.IAM_ACCESS_TOKEN_EXPIRE_MINUTES)
        session = SessionRead(
            id=session_id,
            user_id=user.id,
            organization_id=org,
            browser=user_agent,
            ip_address=ip,
            device=None,
            status="active",
            expires_at=expires,
            revoked_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        await self._sessions.create(session, token_hash=_hash_token(access), refresh_hash=_hash_token(refresh))
        self._metrics.record_login(success=True)
        if org:
            await self._audit.log(
                organization_id=org,
                action="auth.login",
                resource_type="session",
                resource_id=str(session_id),
                actor_user_id=user.id,
                ip_address=ip,
            )
            await self._record_event(org, user.id, SecurityEventType.LOGIN_SUCCESS, ip=ip)
        return AuthTokens(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.IAM_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=membership or user,
            organization_id=org,
        )

    async def register(self, body: RegisterRequest) -> AuthTokens:
        org = await self.provision_organization(body.organization)
        await self.register_user(
            org.id,
            body.user,
            actor_id=None,
        )
        return await self.login(
            LoginRequest(
                email=body.user.email,
                password=body.user.password,
                organization_id=org.id,
            )
        )

    async def refresh_tokens(self, body: RefreshRequest) -> AuthTokens:
        payload = self._tokens.decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise InvalidCredentialsError("Invalid refresh token")
        session_id = UUID(payload["sid"])
        user_id = UUID(payload["sub"])

        session = await self._sessions.get_by_id(session_id)
        if not session:
            raise IamSessionNotFoundError("Session not found")
        if session.status != IamSessionStatus.ACTIVE.value or session.revoked_at is not None:
            raise TokenExpiredError("Session revoked")
        if session.expires_at <= datetime.now(timezone.utc):
            raise TokenExpiredError("Session expired")
        if session.refresh_token_hash != _hash_token(body.refresh_token):
            raise InvalidCredentialsError("Invalid refresh token")

        user = await self._users.get_by_id(user_id)
        if not user:
            raise IamUserNotFoundError(f"User {user_id} not found")
        if user.status != IamUserStatus.ACTIVE.value:
            raise AuthenticationError(f"User account is {user.status}")

        org_id = session.organization_id
        membership = None
        if org_id:
            membership = await self._memberships.get_membership(org_id, user_id)
            if not membership:
                raise InvalidCredentialsError("User is not a member of this organization")

        role_slug = membership.role_slug if membership else SystemRole.VIEWER
        permissions = list(self._rbac.resolve_permissions(role_slug))
        access = self._tokens.create_access_token(
            user_id=user_id,
            organization_id=org_id,
            role_slug=role_slug,
            permissions=permissions,
        )
        refresh = self._tokens.create_refresh_token(user_id=user_id, session_id=session_id)
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.IAM_ACCESS_TOKEN_EXPIRE_MINUTES)
        await self._sessions.update_tokens(
            session_id,
            token_hash=_hash_token(access),
            refresh_hash=_hash_token(refresh),
            expires_at=expires,
        )
        return AuthTokens(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.IAM_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=membership or user,
            organization_id=org_id,
        )

    async def logout(self, access_token: str, *, actor_id: UUID) -> SessionRead:
        session = await self._sessions.get_by_token_hash(_hash_token(access_token))
        if not session:
            raise IamSessionNotFoundError("Session not found")
        if session.user_id != actor_id:
            raise InsufficientPermissionsError("Cannot revoke another user's session")
        return await self.revoke_session(session.id, actor_id=actor_id)

    def build_authentication_service(self) -> AuthenticationService:
        return AuthenticationService(
            organizations=self._orgs,
            users=self._users,
            memberships=self._memberships,
            api_keys=self._api_keys,
            sessions=self._sessions,
            tokens=self._tokens,
            rbac=self._rbac,
        )

    async def get_current_user_profile(self, user_id: UUID, organization_id: UUID) -> CurrentUserRead:
        user = await self._users.get_by_id(user_id)
        if not user:
            raise IamUserNotFoundError(f"User {user_id} not found")
        membership = await self._memberships.get_membership(organization_id, user_id)
        org = await self._orgs.get_by_id(organization_id)
        permissions = list(self._rbac.resolve_permissions(membership.role_slug if membership else SystemRole.VIEWER))
        return CurrentUserRead(
            user=membership or user,
            organization_id=organization_id,
            tenant_id=org.tenant_id if org else None,
            role_slug=membership.role_slug if membership else None,
            permissions=permissions,
        )

    async def create_api_key(
        self, org_id: UUID, data: ApiKeyCreate, *, created_by: UUID
    ) -> ApiKeyCreateResponse:
        await self._require_permission(org_id, created_by, "manage_api_keys")
        full_key, prefix, key_hash = generate_api_key()
        key = await self._api_keys.create(org_id, data, prefix=prefix, key_hash=key_hash, created_by=created_by)
        await self._audit.log(
            organization_id=org_id,
            action="api_key.created",
            resource_type="api_key",
            resource_id=str(key.id),
            actor_user_id=created_by,
        )
        return ApiKeyCreateResponse(**key.model_dump(), secret=full_key)

    async def revoke_api_key(self, org_id: UUID, key_id: UUID, *, actor_id: UUID) -> ApiKeyRead:
        await self._require_permission(org_id, actor_id, "manage_api_keys")
        key = await self._api_keys.revoke(org_id, key_id)
        await self._audit.log(
            organization_id=org_id,
            action="api_key.revoked",
            resource_type="api_key",
            resource_id=str(key_id),
            actor_user_id=actor_id,
        )
        return key

    async def authenticate_api_key(self, raw_key: str) -> tuple[ApiKeyRead, UUID]:
        prefix = raw_key[:12]
        found = await self._api_keys.get_by_prefix(prefix)
        if not found or not verify_api_key(raw_key, found[1]):
            raise ApiKeyNotFoundError("Invalid API key")
        key, _ = found
        await self._api_keys.touch_last_used(key.id)
        self._metrics.api_key_usage_count += 1
        return key, key.organization_id

    async def list_users(self, org_id: UUID, *, actor_id: UUID) -> list[UserRead]:
        await self._require_permission(org_id, actor_id, "manage_users")
        return await self._memberships.list_for_org(org_id)

    async def list_sessions(self, user_id: UUID) -> list[SessionRead]:
        return await self._sessions.list_for_user(user_id)

    async def revoke_session(self, session_id: UUID, *, actor_id: UUID) -> SessionRead:
        session = await self._sessions.revoke(session_id)
        if session.organization_id:
            await self._audit.log(
                organization_id=session.organization_id,
                action="session.revoked",
                resource_type="session",
                resource_id=str(session_id),
                actor_user_id=actor_id,
            )
        return session

    async def get_security_policy(self, org_id: UUID) -> SecurityPolicyRead:
        return await self._policies.get_or_create(org_id)

    async def update_security_policy(
        self, org_id: UUID, data: SecurityPolicyUpdate, *, actor_id: UUID
    ) -> SecurityPolicyRead:
        await self._require_permission(org_id, actor_id, "manage_security")
        policy = await self._policies.update(org_id, data)
        await self._audit.log(
            organization_id=org_id,
            action="security_policy.updated",
            resource_type="security_policy",
            actor_user_id=actor_id,
        )
        return policy

    async def list_permissions(self) -> list[PermissionRead]:
        return [
            PermissionRead(slug=slug, name=meta["name"], category=meta["category"])
            for slug, meta in PERMISSION_CATALOG.items()
        ]

    async def list_roles(self, org_id: UUID) -> list[RoleRead]:
        return await self._roles.list_for_org(org_id)

    async def create_role(self, org_id: UUID, data: RoleCreate, *, actor_id: UUID) -> RoleRead:
        await self._require_permission(org_id, actor_id, "manage_roles")
        role = await self._roles.create(org_id, data)
        await self._audit.log(
            organization_id=org_id,
            action="role.created",
            resource_type="role",
            resource_id=str(role.id),
            actor_user_id=actor_id,
        )
        return role

    async def list_audit_logs(self, org_id: UUID, *, actor_id: UUID, limit: int = 100) -> list[IamAuditRead]:
        await self._require_permission(org_id, actor_id, "view_audit_logs")
        return await self._audit._repository.list_for_org(org_id, limit=limit)

    async def check_permission(self, org_id: UUID, user_id: UUID, permission: str) -> bool:
        self._metrics.record_permission_check()
        membership = await self._memberships.get_membership(org_id, user_id)
        if not membership or not membership.role_slug:
            return False
        return self._rbac.has_permission(membership.role_slug, permission)

    async def list_api_keys(self, org_id: UUID) -> list[ApiKeyRead]:
        return await self._api_keys.list_for_org(org_id)

    async def get_metrics(self, org_id: UUID) -> IamMetricsSnapshot:
        active = 0
        return self._metrics.snapshot(active_sessions=active)

    async def get_organization(self, org_id: UUID) -> OrganizationRead:
        org = await self._orgs.get_by_id(org_id)
        if not org:
            raise OrganizationNotFoundError(f"Organization {org_id} not found")
        return org

    async def get_organization_by_tenant(self, tenant_id: UUID) -> OrganizationRead | None:
        return await self._orgs.get_by_tenant_id(tenant_id)

    async def _require_permission(self, org_id: UUID, user_id: UUID, permission: str) -> None:
        if not await self.check_permission(org_id, user_id, permission):
            self._metrics.policy_violations += 1
            await self._record_event(org_id, user_id, SecurityEventType.PERMISSION_DENIED, payload={"permission": permission})
            raise InsufficientPermissionsError(f"Missing permission: {permission}", permission=permission)

    async def _resolve_default_org(self, user_id: UUID) -> UUID | None:
        return None

    async def _record_event(
        self,
        org_id: UUID | None,
        user_id: UUID | None,
        event_type: SecurityEventType,
        *,
        ip: str | None = None,
        payload: dict | None = None,
    ) -> None:
        if event_type == SecurityEventType.LOGIN_FAILURE:
            self._metrics.security_alerts += 1
        await self._security_events.record(
            SecurityEventRead(
                id=uuid4(),
                organization_id=org_id,
                user_id=user_id,
                event_type=event_type.value,
                severity=SecurityEventSeverity.WARNING.value
                if event_type == SecurityEventType.LOGIN_FAILURE
                else SecurityEventSeverity.INFO.value,
                ip_address=ip,
                payload=payload,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
