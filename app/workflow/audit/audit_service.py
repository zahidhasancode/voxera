"""Workflow audit service."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.workflow.schemas import WorkflowAuditRead, WorkflowEvent


class WorkflowAuditService:
    def __init__(self, repository) -> None:
        self._repository = repository

    async def log_event(
        self,
        *,
        tenant_id: UUID,
        agent_id: UUID,
        event: WorkflowEvent,
        operator: str | None = None,
    ) -> WorkflowAuditRead:
        now = datetime.now(timezone.utc)
        return await self._repository.append(
            WorkflowAuditRead(
                id=uuid4(),
                tenant_id=tenant_id,
                agent_id=agent_id,
                execution_id=event.execution_id,
                conversation_id=event.conversation_id,
                event_type=event.event_type.value,
                payload=event.payload,
                operator=operator,
                occurred_at=event.occurred_at or now,
                created_at=now,
                updated_at=now,
            )
        )

    async def list_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ):
        return await self._repository.list_by_conversation(
            tenant_id, agent_id, conversation_id, limit=limit
        )
