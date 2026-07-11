"""SQLAlchemy knowledge base repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.knowledge import KnowledgeBaseModel
from app.infrastructure.repositories._helpers import apply_partial_update, enum_values
from app.knowledge.repository.knowledge_base_repository import KnowledgeBaseRepository
from app.knowledge.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate


class SqlAlchemyKnowledgeBaseRepository(KnowledgeBaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: KnowledgeBaseCreate) -> KnowledgeBaseRead:
        row = KnowledgeBaseModel(**enum_values(data))
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return KnowledgeBaseRead.model_validate(row)

    async def get_by_id(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
    ) -> KnowledgeBaseRead | None:
        result = await self._session.execute(
            select(KnowledgeBaseModel).where(
                KnowledgeBaseModel.tenant_id == tenant_id,
                KnowledgeBaseModel.id == knowledge_base_id,
            )
        )
        row = result.scalar_one_or_none()
        return KnowledgeBaseRead.model_validate(row) if row else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[KnowledgeBaseRead], int]:
        base = select(KnowledgeBaseModel).where(KnowledgeBaseModel.tenant_id == tenant_id)
        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(KnowledgeBaseModel.created_at.desc()).offset(offset).limit(limit)
        )
        rows = result.scalars().all()
        return [KnowledgeBaseRead.model_validate(r) for r in rows], int(total or 0)

    async def update(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        data: KnowledgeBaseUpdate,
    ) -> KnowledgeBaseRead | None:
        result = await self._session.execute(
            select(KnowledgeBaseModel).where(
                KnowledgeBaseModel.tenant_id == tenant_id,
                KnowledgeBaseModel.id == knowledge_base_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        apply_partial_update(row, data)
        await self._session.flush()
        await self._session.refresh(row)
        return KnowledgeBaseRead.model_validate(row)

    async def delete(self, tenant_id: UUID, knowledge_base_id: UUID) -> bool:
        result = await self._session.execute(
            select(KnowledgeBaseModel).where(
                KnowledgeBaseModel.tenant_id == tenant_id,
                KnowledgeBaseModel.id == knowledge_base_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
