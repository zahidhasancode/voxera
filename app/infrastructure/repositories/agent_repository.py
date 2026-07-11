"""SQLAlchemy agent repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.repository import AgentRepository
from app.agents.schemas import AgentCreate, AgentRead, AgentUpdate
from app.database.models.agent import AgentModel
from app.infrastructure.repositories._helpers import apply_partial_update, enum_values


class SqlAlchemyAgentRepository(AgentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: AgentCreate) -> AgentRead:
        row = AgentModel(**data.model_dump(mode="json", exclude_none=True))
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return AgentRead.model_validate(row)

    async def get_by_id(self, tenant_id: UUID, agent_id: UUID) -> AgentRead | None:
        result = await self._session.execute(
            select(AgentModel).where(
                AgentModel.tenant_id == tenant_id,
                AgentModel.id == agent_id,
            )
        )
        row = result.scalar_one_or_none()
        return AgentRead.model_validate(row) if row else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AgentRead], int]:
        base = select(AgentModel).where(AgentModel.tenant_id == tenant_id)
        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(AgentModel.created_at.desc()).offset(offset).limit(limit)
        )
        rows = result.scalars().all()
        return [AgentRead.model_validate(r) for r in rows], int(total or 0)

    async def update(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        data: AgentUpdate,
    ) -> AgentRead | None:
        result = await self._session.execute(
            select(AgentModel).where(
                AgentModel.tenant_id == tenant_id,
                AgentModel.id == agent_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        apply_partial_update(row, data)
        await self._session.flush()
        await self._session.refresh(row)
        return AgentRead.model_validate(row)

    async def delete(self, tenant_id: UUID, agent_id: UUID) -> bool:
        result = await self._session.execute(
            select(AgentModel).where(
                AgentModel.tenant_id == tenant_id,
                AgentModel.id == agent_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
