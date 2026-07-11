"""Tenant repository interface (port)."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.tenants.schemas import TenantCreate, TenantRead, TenantUpdate


class TenantRepository(ABC):
    """Persistence port for tenants — no business logic."""

    @abstractmethod
    async def create(self, data: TenantCreate) -> TenantRead:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID) -> TenantRead | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(self, slug: str) -> TenantRead | None:
        raise NotImplementedError

    @abstractmethod
    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[TenantRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, tenant_id: UUID, data: TenantUpdate) -> TenantRead | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, tenant_id: UUID) -> bool:
        raise NotImplementedError
