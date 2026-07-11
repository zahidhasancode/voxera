"""SQLAlchemy tenant repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tenant import TenantModel
from app.infrastructure.repositories._helpers import apply_partial_update, enum_values
from app.tenants.repository import TenantRepository
from app.tenants.schemas import TenantCreate, TenantRead, TenantUpdate


class SqlAlchemyTenantRepository(TenantRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: TenantCreate) -> TenantRead:
        payload = enum_values(data)
        metadata = payload.pop("metadata", None)
        row = TenantModel(**payload, metadata_=metadata)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return TenantRead.model_validate(row)

    async def get_by_id(self, tenant_id: UUID) -> TenantRead | None:
        row = await self._session.get(TenantModel, tenant_id)
        return TenantRead.model_validate(row) if row else None

    async def get_by_slug(self, slug: str) -> TenantRead | None:
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.slug == slug)
        )
        row = result.scalar_one_or_none()
        return TenantRead.model_validate(row) if row else None

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[TenantRead], int]:
        total = await self._session.scalar(select(func.count()).select_from(TenantModel))
        result = await self._session.execute(
            select(TenantModel).order_by(TenantModel.created_at.desc()).offset(offset).limit(limit)
        )
        rows = result.scalars().all()
        return [TenantRead.model_validate(r) for r in rows], int(total or 0)

    async def update(self, tenant_id: UUID, data: TenantUpdate) -> TenantRead | None:
        row = await self._session.get(TenantModel, tenant_id)
        if row is None:
            return None
        apply_partial_update(row, data)
        await self._session.flush()
        await self._session.refresh(row)
        return TenantRead.model_validate(row)

    async def delete(self, tenant_id: UUID) -> bool:
        row = await self._session.get(TenantModel, tenant_id)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
