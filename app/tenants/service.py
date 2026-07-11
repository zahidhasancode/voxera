"""Tenant application service interface — business logic in Sprint 2+."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.tenants.schemas import TenantCreate, TenantRead, TenantUpdate


class TenantService(ABC):
    """Application service for tenant lifecycle."""

    @abstractmethod
    async def create_tenant(self, data: TenantCreate) -> TenantRead:
        raise NotImplementedError

    @abstractmethod
    async def get_tenant(self, tenant_id: UUID) -> TenantRead:
        raise NotImplementedError

    @abstractmethod
    async def list_tenants(self, *, offset: int = 0, limit: int = 50) -> tuple[list[TenantRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def update_tenant(self, tenant_id: UUID, data: TenantUpdate) -> TenantRead:
        raise NotImplementedError

    @abstractmethod
    async def delete_tenant(self, tenant_id: UUID) -> None:
        raise NotImplementedError
