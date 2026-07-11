"""Request authentication — JWT and API key validation."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID

from app.core.enums import ApiKeyStatus, IamSessionStatus, IamUserStatus
from app.core.exceptions import (
    ApiKeyNotFoundError,
    AuthenticationError,
    CrossOrganizationAccessError,
    IamSessionNotFoundError,
    IamUserNotFoundError,
    InvalidCredentialsError,
    OrganizationNotFoundError,
    TokenExpiredError,
)
from app.iam.auth.principal import AuthenticatedPrincipal
from app.iam.auth.token_service import TokenService
from app.iam.authorization.rbac_engine import RbacEngine


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthenticationService:
    """Validates JWT and API key credentials into AuthenticatedPrincipal."""

    def __init__(
        self,
        *,
        organizations,
        users,
        memberships,
        api_keys,
        sessions,
        tokens: TokenService | None = None,
        rbac: RbacEngine | None = None,
    ) -> None:
        self._orgs = organizations
        self._users = users
        self._memberships = memberships
        self._api_keys = api_keys
        self._sessions = sessions
        self._tokens = tokens or TokenService()
        self._rbac = rbac or RbacEngine()

    async def authenticate_bearer(self, access_token: str) -> AuthenticatedPrincipal:
        payload = self._tokens.decode_token(access_token)
        if payload.get("type") != "access":
            raise InvalidCredentialsError("Invalid token type")

        user_id = UUID(payload["sub"])
        org_id_raw = payload.get("org")
        if not org_id_raw:
            raise AuthenticationError("Token missing organization context")
        organization_id = UUID(org_id_raw)

        session = await self._sessions.get_by_token_hash(_hash_token(access_token))
        if not session:
            raise IamSessionNotFoundError("Session not found for token")
        self._assert_session_active(session)

        user = await self._users.get_by_id(user_id)
        if not user:
            raise IamUserNotFoundError(f"User {user_id} not found")
        self._assert_user_active(user.status)

        membership = await self._memberships.get_membership(organization_id, user_id)
        if not membership:
            raise CrossOrganizationAccessError("User is not a member of this organization")

        org = await self._orgs.get_by_id(organization_id)
        if not org:
            raise OrganizationNotFoundError(f"Organization {organization_id} not found")

        role_slug = payload.get("role") or membership.role_slug
        permissions = frozenset(payload.get("permissions") or self._rbac.resolve_permissions(role_slug))

        return AuthenticatedPrincipal(
            user_id=user_id,
            organization_id=organization_id,
            tenant_id=org.tenant_id,
            role_slug=role_slug,
            permissions=permissions,
            auth_method="jwt",
            session_id=session.id,
        )

    async def authenticate_api_key(self, raw_key: str) -> AuthenticatedPrincipal:
        prefix = raw_key[:12]
        found = await self._api_keys.get_by_prefix(prefix)
        if not found:
            raise ApiKeyNotFoundError("Invalid API key")

        from app.iam.api_keys.key_crypto import verify_api_key

        key, key_hash = found
        if not verify_api_key(raw_key, key_hash):
            raise ApiKeyNotFoundError("Invalid API key")

        if key.status != ApiKeyStatus.ACTIVE:
            raise AuthenticationError(f"API key is {key.status}")

        if key.expires_at and key.expires_at <= datetime.now(timezone.utc):
            raise AuthenticationError("API key expired")

        org = await self._orgs.get_by_id(key.organization_id)
        if not org:
            raise OrganizationNotFoundError(f"Organization {key.organization_id} not found")

        permissions = frozenset(key.permissions) if key.permissions else frozenset(
            self._rbac.resolve_permissions("developer")
        )

        await self._api_keys.touch_last_used(key.id)

        return AuthenticatedPrincipal(
            user_id=None,
            organization_id=key.organization_id,
            tenant_id=org.tenant_id,
            role_slug="api_key",
            permissions=permissions,
            auth_method="api_key",
            api_key_id=key.id,
        )

    async def validate_organization_access(self, principal: AuthenticatedPrincipal, org_id: UUID) -> None:
        if principal.organization_id != org_id:
            raise CrossOrganizationAccessError("Cross-organization access denied")

    async def validate_tenant_access(self, principal: AuthenticatedPrincipal, tenant_id: UUID) -> None:
        org = await self._orgs.get_by_tenant_id(tenant_id)
        if not org:
            raise OrganizationNotFoundError(f"No organization for tenant {tenant_id}")
        if principal.organization_id != org.id:
            raise CrossOrganizationAccessError("Cross-tenant access denied")
        if principal.tenant_id and principal.tenant_id != tenant_id:
            raise CrossOrganizationAccessError("Cross-tenant access denied")

    def _assert_session_active(self, session) -> None:
        now = datetime.now(timezone.utc)
        if session.status != IamSessionStatus.ACTIVE:
            raise TokenExpiredError("Session revoked")
        if session.revoked_at is not None:
            raise TokenExpiredError("Session revoked")
        if session.expires_at <= now:
            raise TokenExpiredError("Session expired")

    def _assert_user_active(self, status) -> None:
        active = IamUserStatus.ACTIVE.value if hasattr(status, "value") else str(status)
        if active != IamUserStatus.ACTIVE.value:
            raise AuthenticationError(f"User account is {status}")
