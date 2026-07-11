"""SQLAlchemy tool execution repository."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.memory import ToolExecutionModel
from app.memory.repository import ToolExecutionRepository
from app.memory.schemas import AppendToolResultRequest, ToolExecutionRead


class SqlAlchemyToolExecutionRepository(ToolExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        data: AppendToolResultRequest,
    ) -> ToolExecutionRead:
        row = ToolExecutionModel(
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            tool_name=data.tool_name,
            arguments=data.arguments,
            execution_time_ms=data.execution_time_ms,
            status=data.status.value,
            result=data.result,
            error=data.error,
            executed_at=datetime.now(timezone.utc),
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return ToolExecutionRead.model_validate(row)

    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 20,
    ) -> list[ToolExecutionRead]:
        result = await self._session.execute(
            select(ToolExecutionModel)
            .where(
                ToolExecutionModel.tenant_id == tenant_id,
                ToolExecutionModel.agent_id == agent_id,
                ToolExecutionModel.conversation_id == conversation_id,
            )
            .order_by(ToolExecutionModel.created_at.desc())
            .limit(limit)
        )
        return [ToolExecutionRead.model_validate(r) for r in result.scalars().all()]
