"""SQLAlchemy tool audit repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tool_framework import ToolAuditModel
from app.tools.repository.execution import ToolAuditRepository
from app.tools.schemas.execution import ToolAuditRead


class SqlAlchemyToolAuditRepository(ToolAuditRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, audit: ToolAuditRead) -> ToolAuditRead:
        row = ToolAuditModel(
            id=audit.id,
            tenant_id=audit.tenant_id,
            agent_id=audit.agent_id,
            conversation_id=audit.conversation_id,
            execution_id=audit.execution_id,
            tool_slug=audit.tool_slug,
            status=audit.status,
            planner_request=audit.planner_request,
            validated_arguments=audit.validated_arguments,
            execution_result=audit.execution_result,
            execution_duration_ms=audit.execution_duration_ms,
            operator=audit.operator,
            error=audit.error,
            occurred_at=audit.occurred_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return ToolAuditRead.model_validate(row)

    async def list_for_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 100,
    ) -> list[ToolAuditRead]:
        result = await self._session.execute(
            select(ToolAuditModel)
            .where(
                ToolAuditModel.tenant_id == tenant_id,
                ToolAuditModel.agent_id == agent_id,
                ToolAuditModel.conversation_id == conversation_id,
            )
            .order_by(ToolAuditModel.occurred_at.desc())
            .limit(limit)
        )
        return [ToolAuditRead.model_validate(r) for r in result.scalars().all()]
