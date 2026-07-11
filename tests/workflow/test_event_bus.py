"""Event bus tests."""

import pytest

from app.workflow.engine.event_bus import WorkflowEventBus
from app.workflow.schemas import WorkflowEvent
from app.core.enums import WorkflowEventType
from uuid import uuid4
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_event_bus_subscribe_and_emit(monkeypatch):
    monkeypatch.setattr("app.workflow.engine.event_bus.settings.WORKFLOW_ENABLE_EVENT_BUS", True)
    bus = WorkflowEventBus()
    received = []

    async def handler(event: WorkflowEvent) -> None:
        received.append(event)

    bus.subscribe(WorkflowEventType.WORKFLOW_STARTED.value, handler)
    event = WorkflowEvent(
        event_type=WorkflowEventType.WORKFLOW_STARTED,
        execution_id=uuid4(),
        tenant_id=uuid4(),
        agent_id=uuid4(),
        conversation_id=uuid4(),
        payload={"test": True},
        occurred_at=datetime.now(timezone.utc),
    )
    await bus.emit(event)
    assert len(received) == 1
    assert received[0].payload["test"] is True
