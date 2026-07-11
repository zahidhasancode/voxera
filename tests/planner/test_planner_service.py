"""Planner service unit tests with mocked dependencies."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.enums import ConversationStatus, PlannerAction, SessionState, ToolBuiltinSlug
from app.infrastructure.planner.planner_service import PlannerServiceImpl
from app.memory.schemas import PlannerContext, SessionRead
from app.planner.models.structured_model import StructuredPlannerModel
from app.planner.schemas import PlanRequest
from app.tools.schemas.execution import ToolDefinitionRead


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def agent_id():
    return uuid4()


@pytest.fixture
def conversation_id():
    return uuid4()


def _planner_service(tenant_id, agent_id, conversation_id):
    now = datetime.now(timezone.utc)
    memory = AsyncMock()
    memory.get_context = AsyncMock(
        return_value=PlannerContext(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            current_user_message="Hello",
            current_state=SessionState.CALL_STARTED,
            language="en",
        )
    )
    tools = AsyncMock()
    tools.list_tools = AsyncMock(
        return_value=[
            ToolDefinitionRead(
                slug=ToolBuiltinSlug.APPOINTMENT,
                name="Appointment",
                description="Book",
                parameters={},
                permission_scope="appointment",
                enabled=True,
            )
        ]
    )
    sessions = AsyncMock()
    sessions.get_or_create = AsyncMock(
        return_value=AsyncMock(id=uuid4(), reasoning_step_count=0)
    )
    from app.planner.schemas import PlannerSessionRead
    from app.core.enums import PlannerSessionStatus

    sessions.get_or_create = AsyncMock(
        return_value=PlannerSessionRead(
            id=uuid4(),
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            status=PlannerSessionStatus.ACTIVE,
            language="en",
            reasoning_step_count=0,
            last_intent=None,
            created_at=now,
            updated_at=now,
        )
    )
    sessions.increment_steps = AsyncMock(side_effect=lambda sid, **kw: sessions.get_or_create.return_value)
    decisions = AsyncMock()
    decisions.create = AsyncMock(side_effect=lambda d: d)
    history = AsyncMock()
    history.list_by_conversation = AsyncMock(return_value=[])
    history.append = AsyncMock(side_effect=lambda e: e)
    metrics_repo = AsyncMock()
    metrics_repo.snapshot = AsyncMock(return_value={})

    return PlannerServiceImpl(
        memory_manager=memory,
        tool_registry=tools,
        sessions=sessions,
        decisions=decisions,
        history=history,
        metrics_repo=metrics_repo,
        model=StructuredPlannerModel(),
        cache=None,
    )


@pytest.mark.asyncio
async def test_plan_greeting(tenant_id, agent_id, conversation_id):
    service = _planner_service(tenant_id, agent_id, conversation_id)
    plan = await service.plan(
        tenant_id,
        agent_id,
        PlanRequest(conversation_id=conversation_id, user_message="Hello there"),
    )
    assert plan.action == PlannerAction.RESPOND
    assert plan.response
    assert plan.confidence > 0.5


@pytest.mark.asyncio
async def test_plan_appointment_asks_identity(tenant_id, agent_id, conversation_id):
    service = _planner_service(tenant_id, agent_id, conversation_id)
    plan = await service.plan(
        tenant_id,
        agent_id,
        PlanRequest(
            conversation_id=conversation_id,
            user_message="I want to book an appointment",
        ),
    )
    assert plan.action in (PlannerAction.RESPOND, PlannerAction.ASK_CLARIFICATION)
    assert plan.response
