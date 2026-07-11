"""Tool audit logging service."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.enums import ToolAuditStatus
from app.tools.repository.execution import ToolAuditRepository
from app.tools.schemas.execution import ToolAuditRead, ToolExecutionResult


class ToolAuditService:
    def __init__(self, repository: ToolAuditRepository) -> None:
        self._repository = repository

    async def log_request(
        self,
        *,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID | None,
        tool_slug: str,
        planner_request: dict,
        operator: str | None = None,
    ) -> ToolAuditRead:
        return await self._repository.append(
            ToolAuditRead(
                id=uuid4(),
                tenant_id=tenant_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                execution_id=None,
                tool_slug=tool_slug,
                status=ToolAuditStatus.REQUESTED,
                planner_request=planner_request,
                validated_arguments=None,
                execution_result=None,
                execution_duration_ms=None,
                operator=operator,
                error=None,
                occurred_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )

    async def log_outcome(
        self,
        *,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID | None,
        tool_slug: str,
        execution_id: UUID | None,
        status: ToolAuditStatus,
        validated_arguments: dict | None,
        result: ToolExecutionResult | None,
        duration_ms: float | None,
        operator: str | None = None,
        error: str | None = None,
    ) -> ToolAuditRead:
        return await self._repository.append(
            ToolAuditRead(
                id=uuid4(),
                tenant_id=tenant_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                execution_id=execution_id,
                tool_slug=tool_slug,
                status=status,
                planner_request=None,
                validated_arguments=validated_arguments,
                execution_result=result.model_dump(mode="json") if result else None,
                execution_duration_ms=duration_ms,
                operator=operator,
                error=error,
                occurred_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
