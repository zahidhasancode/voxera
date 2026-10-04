"""SQLAlchemy IAM repositories."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ApiKeyStatus, IamMembershipStatus, IamSessionStatus, IamUserStatus
from app.database.models.iam import (
    IamApiKeyModel,
    IamAuditLogModel,
    IamSecurityEventModel,
    IamSecurityPolicyModel,
    IamSessionModel,
    IamUserModel,
    OrganizationMembershipModel,
    OrganizationModel,
    IamRoleModel,
)
from app.iam.repository import (
    ApiKeyRepository,
    IamAuditRepository,
    MembershipRepository,
    OrganizationRepository,
    RoleRepository,
    SecurityEventRepository,
    SecurityPolicyRepository,
    SessionRepository,
    UserRepository,
)
from app.iam.schemas import (
    ApiKeyCreate,
    ApiKeyRead,
    IamAuditRead,
    OrganizationCreate,
    OrganizationRead,
    RoleCreate,
    RoleRead,
    SecurityEventRead,
    SecurityPolicyRead,
    SecurityPolicyUpdate,
    SessionRead,
    UserCreate,
    UserInvite,
    UserRead,
)


class SqlAlchemyOrganizationRepository(OrganizationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: OrganizationCreate) -> OrganizationRead:
        row = OrganizationModel(
            tenant_id=data.tenant_id,
            company_name=data.company_name,
            slug=data.slug,
            plan=data.plan,
            region=data.region,
            owner_user_id=data.owner_user_id,
            timezone=data.timezone,
            language=data.language,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return OrganizationRead.model_validate(row)

    async def get_by_id(self, org_id: UUID) -> OrganizationRead | None:
        row = await self._session.get(OrganizationModel, org_id)
        return OrganizationRead.model_validate(row) if row else None

    async def get_by_tenant_id(self, tenant_id: UUID) -> OrganizationRead | None:
        result = await self._session.execute(
            select(OrganizationModel).where(OrganizationModel.tenant_id == tenant_id)
        )
        row = result.scalar_one_or_none()
        return OrganizationRead.model_validate(row) if row else None

    async def list_all(self, *, limit: int = 100) -> list[OrganizationRead]:
        result = await self._session.execute(select(OrganizationModel).limit(limit))
        return [OrganizationRead.model_validate(r) for r in result.scalars().all()]


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: UserCreate, password_hash: str) -> UserRead:
        row = IamUserModel(
            email=data.email.lower(),
            password_hash=password_hash,
            name=data.name,
            status=IamUserStatus.ACTIVE,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return UserRead.model_validate(row)

    async def get_by_id(self, user_id: UUID) -> UserRead | None:
        row = await self._session.get(IamUserModel, user_id)
        return UserRead.model_validate(row) if row else None

    async def get_by_email(self, email: str) -> tuple[UserRead, str | None] | None:
        result = await self._session.execute(
            select(IamUserModel).where(IamUserModel.email == email.lower())
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return UserRead.model_validate(row), row.password_hash

    async def update_last_login(self, user_id: UUID) -> None:
        row = await self._session.get(IamUserModel, user_id)
        if row:
            row.last_login_at = datetime.now(timezone.utc)


class SqlAlchemyMembershipRepository(MembershipRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, org_id: UUID, user_id: UUID, invite: UserInvite) -> UserRead:
        now = datetime.now(timezone.utc)
        membership = OrganizationMembershipModel(
            organization_id=org_id,
            user_id=user_id,
            role_slug=invite.role_slug,
            department=invite.department,
            title=invite.title,
            status=IamMembershipStatus.ACTIVE,
            joined_at=now,
        )
        self._session.add(membership)
        user = await self._session.get(IamUserModel, user_id)
        await self._session.flush()
        read = UserRead.model_validate(user)
        read.role_slug = invite.role_slug
        read.department = invite.department
        read.title = invite.title
        return read

    async def list_for_org(self, org_id: UUID) -> list[UserRead]:
        result = await self._session.execute(
            select(IamUserModel, OrganizationMembershipModel)
            .join(OrganizationMembershipModel, OrganizationMembershipModel.user_id == IamUserModel.id)
            .where(OrganizationMembershipModel.organization_id == org_id)
        )
        users = []
        for user, mem in result.all():
            read = UserRead.model_validate(user)
            read.role_slug = mem.role_slug
            read.department = mem.department
            read.title = mem.title
            users.append(read)
        return users

    async def get_membership(self, org_id: UUID, user_id: UUID) -> UserRead | None:
        result = await self._session.execute(
            select(IamUserModel, OrganizationMembershipModel)
            .join(OrganizationMembershipModel, OrganizationMembershipModel.user_id == IamUserModel.id)
            .where(
                OrganizationMembershipModel.organization_id == org_id,
                OrganizationMembershipModel.user_id == user_id,
            )
        )
        row = result.first()
        if not row:
            return None
        user, mem = row
        read = UserRead.model_validate(user)
        read.role_slug = mem.role_slug
        read.department = mem.department
        read.title = mem.title
        return read

    async def update_role(self, org_id: UUID, user_id: UUID, role_slug: str) -> UserRead:
        result = await self._session.execute(
            select(OrganizationMembershipModel).where(
                OrganizationMembershipModel.organization_id == org_id,
                OrganizationMembershipModel.user_id == user_id,
            )
        )
        mem = result.scalar_one()
        mem.role_slug = role_slug
        return await self.get_membership(org_id, user_id)  # type: ignore[return-value]


class SqlAlchemyRoleRepository(RoleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, org_id: UUID, data: RoleCreate) -> RoleRead:
        row = IamRoleModel(
            organization_id=org_id,
            slug=data.slug,
            name=data.name,
            description=data.description,
            is_system=False,
            inherits_from=data.inherits_from,
            permissions=data.permissions,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return RoleRead.model_validate(row)

    async def list_for_org(self, org_id: UUID) -> list[RoleRead]:
        result = await self._session.execute(
            select(IamRoleModel).where(
                (IamRoleModel.organization_id == org_id) | (IamRoleModel.organization_id.is_(None))
            )
        )
        return [RoleRead.model_validate(r) for r in result.scalars().all()]


class SqlAlchemyApiKeyRepository(ApiKeyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, org_id: UUID, data: ApiKeyCreate, *, prefix: str, key_hash: str, created_by: UUID | None
    ) -> ApiKeyRead:
        row = IamApiKeyModel(
            organization_id=org_id,
            name=data.name,
            key_prefix=prefix,
            key_hash=key_hash,
            scopes=data.scopes,
            permissions=data.permissions,
            environment=data.environment.value,
            created_by=created_by,
            expires_at=data.expires_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return ApiKeyRead.model_validate(row)

    async def list_for_org(self, org_id: UUID) -> list[ApiKeyRead]:
        result = await self._session.execute(
            select(IamApiKeyModel).where(IamApiKeyModel.organization_id == org_id)
        )
        return [ApiKeyRead.model_validate(r) for r in result.scalars().all()]

    async def get_by_prefix(self, prefix: str) -> tuple[ApiKeyRead, str] | None:
        result = await self._session.execute(
            select(IamApiKeyModel).where(
                IamApiKeyModel.key_prefix == prefix,
                IamApiKeyModel.status == ApiKeyStatus.ACTIVE.value,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return ApiKeyRead.model_validate(row), row.key_hash

    async def revoke(self, org_id: UUID, key_id: UUID) -> ApiKeyRead:
        result = await self._session.execute(
            select(IamApiKeyModel).where(IamApiKeyModel.organization_id == org_id, IamApiKeyModel.id == key_id)
        )
        row = result.scalar_one()
        row.status = ApiKeyStatus.REVOKED.value
        await self._session.flush()
        return ApiKeyRead.model_validate(row)

    async def touch_last_used(self, key_id: UUID) -> None:
        row = await self._session.get(IamApiKeyModel, key_id)
        if row:
            row.last_used_at = datetime.now(timezone.utc)


class SqlAlchemySessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, session: SessionRead, *, token_hash: str, refresh_hash: str | None) -> SessionRead:
        row = IamSessionModel(
            id=session.id,
            user_id=session.user_id,
            organization_id=session.organization_id,
            token_hash=token_hash,
            refresh_token_hash=refresh_hash,
            browser=session.browser,
            ip_address=session.ip_address,
            country=session.country,
            device=session.device,
            expires_at=session.expires_at,
        )
        self._session.add(row)
        await self._session.flush()
        return session

    async def list_for_user(self, user_id: UUID) -> list[SessionRead]:
        result = await self._session.execute(
            select(IamSessionModel).where(IamSessionModel.user_id == user_id)
        )
        return [SessionRead.model_validate(r) for r in result.scalars().all()]

    async def revoke(self, session_id: UUID) -> SessionRead:
        row = await self._session.get(IamSessionModel, session_id)
        row.status = IamSessionStatus.REVOKED.value
        row.revoked_at = datetime.now(timezone.utc)
        await self._session.flush()
        return SessionRead.model_validate(row)

    async def count_active_for_user(self, user_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(IamSessionModel).where(
                IamSessionModel.user_id == user_id,
                IamSessionModel.status == IamSessionStatus.ACTIVE.value,
            )
        )
        return int(result.scalar_one())

    async def get_by_token_hash(self, token_hash: str) -> SessionRead | None:
        result = await self._session.execute(
            select(IamSessionModel).where(IamSessionModel.token_hash == token_hash)
        )
        row = result.scalar_one_or_none()
        return SessionRead.model_validate(row) if row else None

    async def get_by_id(self, session_id: UUID) -> SessionRead | None:
        row = await self._session.get(IamSessionModel, session_id)
        return SessionRead.model_validate(row) if row else None

    async def get_by_refresh_hash(self, refresh_hash: str) -> SessionRead | None:
        result = await self._session.execute(
            select(IamSessionModel).where(IamSessionModel.refresh_token_hash == refresh_hash)
        )
        row = result.scalar_one_or_none()
        return SessionRead.model_validate(row) if row else None

    async def update_tokens(
        self,
        session_id: UUID,
        *,
        token_hash: str,
        refresh_hash: str,
        expires_at: datetime,
    ) -> SessionRead:
        row = await self._session.get(IamSessionModel, session_id)
        if not row:
            raise ValueError(f"Session {session_id} not found")
        row.token_hash = token_hash
        row.refresh_token_hash = refresh_hash
        row.expires_at = expires_at
        row.status = IamSessionStatus.ACTIVE.value
        row.revoked_at = None
        await self._session.flush()
        return SessionRead.model_validate(row)


class SqlAlchemySecurityPolicyRepository(SecurityPolicyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, org_id: UUID) -> SecurityPolicyRead:
        result = await self._session.execute(
            select(IamSecurityPolicyModel).where(IamSecurityPolicyModel.organization_id == org_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            row = IamSecurityPolicyModel(organization_id=org_id)
            self._session.add(row)
            await self._session.flush()
            await self._session.refresh(row)
        return SecurityPolicyRead.model_validate(row)

    async def update(self, org_id: UUID, data: SecurityPolicyUpdate) -> SecurityPolicyRead:
        await self.get_or_create(org_id)
        result = await self._session.execute(
            select(IamSecurityPolicyModel).where(IamSecurityPolicyModel.organization_id == org_id)
        )
        row = result.scalar_one()
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return SecurityPolicyRead.model_validate(row)


class SqlAlchemyIamAuditRepository(IamAuditRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, entry: IamAuditRead) -> IamAuditRead:
        row = IamAuditLogModel(
            id=entry.id,
            organization_id=entry.organization_id,
            actor_user_id=entry.actor_user_id,
            actor_type=entry.actor_type,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            ip_address=entry.ip_address,
            payload=entry.payload,
            occurred_at=entry.occurred_at,
        )
        self._session.add(row)
        await self._session.flush()
        return entry

    async def list_for_org(self, org_id: UUID, *, limit: int = 100) -> list[IamAuditRead]:
        result = await self._session.execute(
            select(IamAuditLogModel)
            .where(IamAuditLogModel.organization_id == org_id)
            .order_by(IamAuditLogModel.occurred_at.desc())
            .limit(limit)
        )
        return [IamAuditRead.model_validate(r) for r in result.scalars().all()]


class SqlAlchemySecurityEventRepository(SecurityEventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, event: SecurityEventRead) -> SecurityEventRead:
        row = IamSecurityEventModel(
            id=event.id,
            organization_id=event.organization_id,
            user_id=event.user_id,
            event_type=event.event_type,
            severity=event.severity,
            ip_address=event.ip_address,
            payload=event.payload,
        )
        self._session.add(row)
        await self._session.flush()
        return event

    async def list_for_org(self, org_id: UUID, *, limit: int = 100) -> list[SecurityEventRead]:
        result = await self._session.execute(
            select(IamSecurityEventModel)
            .where(IamSecurityEventModel.organization_id == org_id)
            .order_by(IamSecurityEventModel.created_at.desc())
            .limit(limit)
        )
        return [SecurityEventRead.model_validate(r) for r in result.scalars().all()]
