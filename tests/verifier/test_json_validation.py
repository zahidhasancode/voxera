"""JSON schema validation tests."""

from app.core.enums import PlannerAction, PlannerIntent
from app.planner.schemas import ExecutionPlan, PlannerPlan
from app.verifier.validators.json_validator import JsonSchemaValidator
from app.verifier.schemas import ValidationContext, VerifierInput
from uuid import uuid4


def test_missing_tool_call_for_call_tool():
    plan = PlannerPlan(
        intent=PlannerIntent.APPOINTMENT,
        confidence=0.9,
        reasoning=["book"],
        next_action="book",
        action=PlannerAction.CALL_TOOL,
        tool_call=None,
        plan=ExecutionPlan(goal="book"),
    )
    ctx = ValidationContext(
        verifier_input=VerifierInput(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            agent_id=uuid4(),
            planner_output=plan,
            current_state=__import__("app.core.enums", fromlist=["SessionState"]).SessionState.CALL_STARTED,
        )
    )
    violations = JsonSchemaValidator().validate(plan, ctx)
    assert any("missing_tool_call" in v for v in violations)
