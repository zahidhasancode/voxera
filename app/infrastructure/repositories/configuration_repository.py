"""SQLAlchemy agent configuration repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.configuration.repository import AgentConfigurationRepository
from app.configuration.schemas import (
    AgentConfigurationCreate,
    AgentConfigurationRead,
    AgentConfigurationUpdate,
)
from app.database.models.configuration import AgentConfigurationModel
from app.infrastructure.repositories._helpers import apply_partial_update, enum_values


def _to_read(row: AgentConfigurationModel) -> AgentConfigurationRead:
    return AgentConfigurationRead.model_validate(row)


class SqlAlchemyAgentConfigurationRepository(AgentConfigurationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: AgentConfigurationCreate) -> AgentConfigurationRead:
        payload = enum_values(data)
        if payload.get("allowed_tool_ids") is not None:
            payload["allowed_tool_ids"] = [str(v) for v in payload["allowed_tool_ids"]]
        row = AgentConfigurationModel(**payload)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_read(row)

    async def get_by_agent_id(
        self,
        tenant_id: UUID,
        agent_id: UUID,
    ) -> AgentConfigurationRead | None:
        result = await self._session.execute(
            select(AgentConfigurationModel).where(
                AgentConfigurationModel.tenant_id == tenant_id,
                AgentConfigurationModel.agent_id == agent_id,
            )
        )
        row = result.scalar_one_or_none()
        return _to_read(row) if row else None

    async def update(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        data: AgentConfigurationUpdate,
    ) -> AgentConfigurationRead | None:
        result = await self._session.execute(
            select(AgentConfigurationModel).where(
                AgentConfigurationModel.tenant_id == tenant_id,
                AgentConfigurationModel.agent_id == agent_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        apply_partial_update(row, data)
        if data.allowed_tool_ids is not None:
            row.allowed_tool_ids = [str(v) for v in data.allowed_tool_ids]
        await self._session.flush()
        await self._session.refresh(row)
        return _to_read(row)

    async def delete(self, tenant_id: UUID, agent_id: UUID) -> bool:
        result = await self._session.execute(
            select(AgentConfigurationModel).where(
                AgentConfigurationModel.tenant_id == tenant_id,
                AgentConfigurationModel.agent_id == agent_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
