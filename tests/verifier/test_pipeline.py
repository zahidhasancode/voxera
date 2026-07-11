"""Full validation pipeline tests."""

from uuid import uuid4

from app.core.enums import PlannerAction, PlannerIntent, SessionState, VerifierOutcome
from app.planner.schemas import ExecutionPlan, PlannerPlan
from app.tools.schemas.execution import ToolDefinitionRead
from app.verifier.schemas import VerifierInput
from app.verifier.validators.pipeline import ValidationPipeline


def test_pipeline_approves_greeting():
    plan = PlannerPlan(
        intent=PlannerIntent.GREETING,
        confidence=0.92,
        reasoning=["User greeted"],
        next_action="respond",
        action=PlannerAction.RESPOND,
        response="Hello! How can I help?",
        plan=ExecutionPlan(goal="Greet customer"),
    )
    inp = VerifierInput(
        conversation_id=uuid4(),
        tenant_id=uuid4(),
        agent_id=uuid4(),
        planner_output=plan,
        allowed_tools=[],
        current_state=SessionState.CALL_STARTED,
    )
    _, result = ValidationPipeline().run(inp)
    assert result.approved is True
    assert result.outcome == VerifierOutcome.APPROVED


def test_pipeline_rejects_unknown_tool():
    from app.planner.schemas import ToolCallPlan

    plan = PlannerPlan(
        intent=PlannerIntent.APPOINTMENT,
        confidence=0.9,
        reasoning=["book"],
        next_action="book",
        action=PlannerAction.CALL_TOOL,
        tool_call=ToolCallPlan(tool_slug="nonexistent_tool", arguments={"action": "book"}),
        plan=ExecutionPlan(goal="book"),
    )
    inp = VerifierInput(
        conversation_id=uuid4(),
        tenant_id=uuid4(),
        agent_id=uuid4(),
        planner_output=plan,
        allowed_tools=[
            ToolDefinitionRead(
                slug="appointment",
                name="Appointment",
                description="",
                parameters={"type": "object", "properties": {"action": {"type": "string"}}, "required": ["action"]},
                permission_scope="appointment",
            )
        ],
        current_state=SessionState.CALL_STARTED,
    )
    _, result = ValidationPipeline().run(inp)
    assert result.approved is False
    assert result.outcome == VerifierOutcome.REJECTED
