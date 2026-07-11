"""AuthenticationService unit tests."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.enums import ApiKeyStatus, IamSessionStatus, IamUserStatus
from app.core.exceptions import CrossOrganizationAccessError, TokenExpiredError
from app.iam.auth.authentication_service import AuthenticationService
from app.iam.auth.token_service import TokenService
from app.iam.schemas import OrganizationRead, SessionRead, UserRead


class _FakeOrgs:
    def __init__(self, org: OrganizationRead):
        self._org = org

    async def get_by_id(self, org_id):
        return self._org if self._org.id == org_id else None

    async def get_by_tenant_id(self, tenant_id):
        return self._org if self._org.tenant_id == tenant_id else None


class _FakeUsers:
    def __init__(self, user: UserRead):
        self._user = user

    async def get_by_id(self, user_id):
        return self._user if self._user.id == user_id else None


class _FakeMemberships:
    def __init__(self, org_id, user_id, role_slug: str):
        self.org_id = org_id
        self.user_id = user_id
        self.role_slug = role_slug

    async def get_membership(self, org_id, user_id):
        if org_id == self.org_id and user_id == self.user_id:
            return UserRead(
                id=user_id,
                email="user@example.com",
                name="User",
                avatar_url=None,
                status=IamUserStatus.ACTIVE,
                mfa_enabled=False,
                last_login_at=None,
                role_slug=self.role_slug,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        return None


class _FakeSessions:
    def __init__(self, session: SessionRead, token_hash: str):
        self._session = session
        self._token_hash = token_hash

    async def get_by_token_hash(self, token_hash: str):
        return self._session if token_hash == self._token_hash else None


class _FakeApiKeys:
    async def get_by_prefix(self, prefix: str):
        return None

    async def touch_last_used(self, key_id):
        return None


def _hash_token(token: str) -> str:
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()


@pytest.mark.asyncio
async def test_authenticate_bearer_success():
    user_id = uuid4()
    org_id = uuid4()
    tenant_id = uuid4()
    session_id = uuid4()
    tokens = TokenService()
    access = tokens.create_access_token(
        user_id=user_id,
        organization_id=org_id,
        role_slug="viewer",
        permissions=["view_calls"],
    )
    now = datetime.now(timezone.utc)
    session = SessionRead(
        id=session_id,
        user_id=user_id,
        organization_id=org_id,
        browser=None,
        ip_address=None,
        country=None,
        device=None,
        status=IamSessionStatus.ACTIVE,
        expires_at=now + timedelta(hours=1),
        revoked_at=None,
        created_at=now,
        updated_at=now,
    )
    org = OrganizationRead(
        id=org_id,
        tenant_id=tenant_id,
        company_name="Acme",
        slug="acme",
        plan="free",
        status="active",
        region=None,
        owner_user_id=user_id,
        timezone="UTC",
        language="en",
        created_at=now,
        updated_at=now,
    )
    user = UserRead(
        id=user_id,
        email="user@example.com",
        name="User",
        avatar_url=None,
        status=IamUserStatus.ACTIVE,
        mfa_enabled=False,
        last_login_at=None,
        created_at=now,
        updated_at=now,
    )
    auth = AuthenticationService(
        organizations=_FakeOrgs(org),
        users=_FakeUsers(user),
        memberships=_FakeMemberships(org_id, user_id, "viewer"),
        api_keys=_FakeApiKeys(),
        sessions=_FakeSessions(session, _hash_token(access)),
        tokens=tokens,
    )
    principal = await auth.authenticate_bearer(access)
    assert principal.user_id == user_id
    assert principal.organization_id == org_id
    assert principal.tenant_id == tenant_id
    assert principal.has_permission("view_calls")


@pytest.mark.asyncio
async def test_authenticate_bearer_rejects_revoked_session():
    user_id = uuid4()
    org_id = uuid4()
    session_id = uuid4()
    tokens = TokenService()
    access = tokens.create_access_token(user_id=user_id, organization_id=org_id, role_slug="viewer")
    now = datetime.now(timezone.utc)
    session = SessionRead(
        id=session_id,
        user_id=user_id,
        organization_id=org_id,
        browser=None,
        ip_address=None,
        country=None,
        device=None,
        status=IamSessionStatus.REVOKED,
        expires_at=now + timedelta(hours=1),
        revoked_at=now,
        created_at=now,
        updated_at=now,
    )
    org = OrganizationRead(
        id=org_id,
        tenant_id=uuid4(),
        company_name="Acme",
        slug="acme",
        plan="free",
        status="active",
        region=None,
        owner_user_id=user_id,
        timezone="UTC",
        language="en",
        created_at=now,
        updated_at=now,
    )
    user = UserRead(
        id=user_id,
        email="user@example.com",
        name="User",
        avatar_url=None,
        status=IamUserStatus.ACTIVE,
        mfa_enabled=False,
        last_login_at=None,
        created_at=now,
        updated_at=now,
    )
    auth = AuthenticationService(
        organizations=_FakeOrgs(org),
        users=_FakeUsers(user),
        memberships=_FakeMemberships(org_id, user_id, "viewer"),
        api_keys=_FakeApiKeys(),
        sessions=_FakeSessions(session, _hash_token(access)),
        tokens=tokens,
    )
    with pytest.raises(TokenExpiredError):
        await auth.authenticate_bearer(access)


@pytest.mark.asyncio
async def test_validate_tenant_access_rejects_cross_tenant():
    org_a = uuid4()
    org_b = uuid4()
    tenant_a = uuid4()
    tenant_b = uuid4()
    now = datetime.now(timezone.utc)

    class _MultiOrgs:
        async def get_by_tenant_id(self, tenant_id):
            if tenant_id == tenant_a:
                return OrganizationRead(
                    id=org_a,
                    tenant_id=tenant_a,
                    company_name="A",
                    slug="a",
                    plan="free",
                    status="active",
                    region=None,
                    owner_user_id=uuid4(),
                    timezone="UTC",
                    language="en",
                    created_at=now,
                    updated_at=now,
                )
            if tenant_id == tenant_b:
                return OrganizationRead(
                    id=org_b,
                    tenant_id=tenant_b,
                    company_name="B",
                    slug="b",
                    plan="free",
                    status="active",
                    region=None,
                    owner_user_id=uuid4(),
                    timezone="UTC",
                    language="en",
                    created_at=now,
                    updated_at=now,
                )
            return None

        async def get_by_id(self, org_id):
            return None

    auth = AuthenticationService(
        organizations=_MultiOrgs(),
        users=_FakeUsers(
            UserRead(
                id=uuid4(),
                email="u@example.com",
                name="U",
                avatar_url=None,
                status=IamUserStatus.ACTIVE,
                mfa_enabled=False,
                last_login_at=None,
                created_at=now,
                updated_at=now,
            )
        ),
        memberships=_FakeMemberships(org_a, uuid4(), "viewer"),
        api_keys=_FakeApiKeys(),
        sessions=_FakeSessions(
            SessionRead(
                id=uuid4(),
                user_id=uuid4(),
                organization_id=org_a,
                browser=None,
                ip_address=None,
                country=None,
                device=None,
                status=IamSessionStatus.ACTIVE,
                expires_at=now + timedelta(hours=1),
                revoked_at=None,
                created_at=now,
                updated_at=now,
            ),
            "unused",
        ),
    )
    from app.iam.auth.principal import AuthenticatedPrincipal

    principal = AuthenticatedPrincipal(
        user_id=uuid4(),
        organization_id=org_a,
        tenant_id=tenant_a,
        role_slug="viewer",
        permissions=frozenset({"view_calls"}),
        auth_method="jwt",
    )
    with pytest.raises(CrossOrganizationAccessError):
        await auth.validate_tenant_access(principal, tenant_b)
