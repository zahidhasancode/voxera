"""Tenant service implementation — persistence delegation only (Sprint 2 adds rules)."""

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.repositories.tenant_repository import SqlAlchemyTenantRepository
from app.tenants.schemas import TenantCreate, TenantRead, TenantUpdate
from app.tenants.service import TenantService


class TenantServiceImpl(TenantService):
    def __init__(self, repository: SqlAlchemyTenantRepository) -> None:
        self._repository = repository

    async def create_tenant(self, data: TenantCreate) -> TenantRead:
        return await self._repository.create(data)

    async def get_tenant(self, tenant_id: UUID) -> TenantRead:
        row = await self._repository.get_by_id(tenant_id)
        if row is None:
            raise NotFoundError(f"Tenant {tenant_id} not found")
        return row

    async def list_tenants(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[TenantRead], int]:
        return await self._repository.list(offset=offset, limit=limit)

    async def update_tenant(self, tenant_id: UUID, data: TenantUpdate) -> TenantRead:
        row = await self._repository.update(tenant_id, data)
        if row is None:
            raise NotFoundError(f"Tenant {tenant_id} not found")
        return row

    async def delete_tenant(self, tenant_id: UUID) -> None:
        deleted = await self._repository.delete(tenant_id)
        if not deleted:
            raise NotFoundError(f"Tenant {tenant_id} not found")
