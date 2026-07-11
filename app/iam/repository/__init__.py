"""IAM repository ports."""

from abc import ABC, abstractmethod
from uuid import UUID

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


class OrganizationRepository(ABC):
    @abstractmethod
    async def create(self, data: OrganizationCreate) -> OrganizationRead: ...
    @abstractmethod
    async def get_by_id(self, org_id: UUID) -> OrganizationRead | None: ...
    @abstractmethod
    async def get_by_tenant_id(self, tenant_id: UUID) -> OrganizationRead | None: ...
    @abstractmethod
    async def list_all(self, *, limit: int = 100) -> list[OrganizationRead]: ...


class UserRepository(ABC):
    @abstractmethod
    async def create(self, data: UserCreate, password_hash: str) -> UserRead: ...
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> UserRead | None: ...
    @abstractmethod
    async def get_by_email(self, email: str) -> tuple[UserRead, str | None] | None: ...
    @abstractmethod
    async def update_last_login(self, user_id: UUID) -> None: ...


class MembershipRepository(ABC):
    @abstractmethod
    async def add(self, org_id: UUID, user_id: UUID, invite: UserInvite) -> UserRead: ...
    @abstractmethod
    async def list_for_org(self, org_id: UUID) -> list[UserRead]: ...
    @abstractmethod
    async def get_membership(self, org_id: UUID, user_id: UUID) -> UserRead | None: ...
    @abstractmethod
    async def update_role(self, org_id: UUID, user_id: UUID, role_slug: str) -> UserRead: ...


class RoleRepository(ABC):
    @abstractmethod
    async def create(self, org_id: UUID, data: RoleCreate) -> RoleRead: ...
    @abstractmethod
    async def list_for_org(self, org_id: UUID) -> list[RoleRead]: ...


class ApiKeyRepository(ABC):
    @abstractmethod
    async def create(self, org_id: UUID, data: ApiKeyCreate, *, prefix: str, key_hash: str, created_by: UUID | None) -> ApiKeyRead: ...
    @abstractmethod
    async def list_for_org(self, org_id: UUID) -> list[ApiKeyRead]: ...
    @abstractmethod
    async def get_by_prefix(self, prefix: str) -> tuple[ApiKeyRead, str] | None: ...
    @abstractmethod
    async def revoke(self, org_id: UUID, key_id: UUID) -> ApiKeyRead: ...
    @abstractmethod
    async def touch_last_used(self, key_id: UUID) -> None: ...


class SessionRepository(ABC):
    @abstractmethod
    async def create(self, session: SessionRead, *, token_hash: str, refresh_hash: str | None) -> SessionRead: ...
    @abstractmethod
    async def list_for_user(self, user_id: UUID) -> list[SessionRead]: ...
    @abstractmethod
    async def revoke(self, session_id: UUID) -> SessionRead: ...
    @abstractmethod
    async def count_active_for_user(self, user_id: UUID) -> int: ...
    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> SessionRead | None: ...
    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> SessionRead | None: ...
    @abstractmethod
    async def get_by_refresh_hash(self, refresh_hash: str) -> SessionRead | None: ...
    @abstractmethod
    async def update_tokens(
        self,
        session_id: UUID,
        *,
        token_hash: str,
        refresh_hash: str,
        expires_at,
    ) -> SessionRead: ...


class SecurityPolicyRepository(ABC):
    @abstractmethod
    async def get_or_create(self, org_id: UUID) -> SecurityPolicyRead: ...
    @abstractmethod
    async def update(self, org_id: UUID, data: SecurityPolicyUpdate) -> SecurityPolicyRead: ...


class IamAuditRepository(ABC):
    @abstractmethod
    async def append(self, entry: IamAuditRead) -> IamAuditRead: ...
    @abstractmethod
    async def list_for_org(self, org_id: UUID, *, limit: int = 100) -> list[IamAuditRead]: ...


class SecurityEventRepository(ABC):
    @abstractmethod
    async def record(self, event: SecurityEventRead) -> SecurityEventRead: ...
    @abstractmethod
    async def list_for_org(self, org_id: UUID, *, limit: int = 100) -> list[SecurityEventRead]: ...
