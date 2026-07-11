"""SQLAlchemy tool registry repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tool import ToolModel
from app.infrastructure.repositories._helpers import apply_partial_update, enum_values
from app.tools.repository import ToolRepository
from app.tools.schemas import ToolCreate, ToolRead, ToolUpdate


class SqlAlchemyToolRepository(ToolRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ToolCreate) -> ToolRead:
        row = ToolModel(**enum_values(data))
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return ToolRead.model_validate(row)

    async def get_by_id(self, tenant_id: UUID, tool_id: UUID) -> ToolRead | None:
        result = await self._session.execute(
            select(ToolModel).where(
                ToolModel.tenant_id == tenant_id,
                ToolModel.id == tool_id,
            )
        )
        row = result.scalar_one_or_none()
        return ToolRead.model_validate(row) if row else None

    async def get_by_slug(self, tenant_id: UUID, slug: str) -> ToolRead | None:
        result = await self._session.execute(
            select(ToolModel).where(
                ToolModel.tenant_id == tenant_id,
                ToolModel.slug == slug,
            )
        )
        row = result.scalar_one_or_none()
        return ToolRead.model_validate(row) if row else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[ToolRead], int]:
        base = select(ToolModel).where(ToolModel.tenant_id == tenant_id)
        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(ToolModel.created_at.desc()).offset(offset).limit(limit)
        )
        rows = result.scalars().all()
        return [ToolRead.model_validate(r) for r in rows], int(total or 0)

    async def update(
        self,
        tenant_id: UUID,
        tool_id: UUID,
        data: ToolUpdate,
    ) -> ToolRead | None:
        result = await self._session.execute(
            select(ToolModel).where(
                ToolModel.tenant_id == tenant_id,
                ToolModel.id == tool_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        apply_partial_update(row, data)
        await self._session.flush()
        await self._session.refresh(row)
        return ToolRead.model_validate(row)

    async def delete(self, tenant_id: UUID, tool_id: UUID) -> bool:
        result = await self._session.execute(
            select(ToolModel).where(
                ToolModel.tenant_id == tenant_id,
                ToolModel.id == tool_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
