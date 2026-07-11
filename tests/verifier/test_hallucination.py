"""Hallucination detection tests."""

from uuid import uuid4

from app.core.enums import PlannerAction, PlannerIntent, SessionState
from app.planner.schemas import ExecutionPlan, PlannerPlan, ToolCallPlan
from app.verifier.validators.hallucination_detector import HallucinationDetector
from app.verifier.schemas import ValidationContext, VerifierInput


def test_unknown_tool_detected():
    plan = PlannerPlan(
        intent=PlannerIntent.APPOINTMENT,
        confidence=0.9,
        reasoning=["x"],
        next_action="x",
        action=PlannerAction.CALL_TOOL,
        tool_call=ToolCallPlan(tool_slug="fake_tool", arguments={}),
        plan=ExecutionPlan(goal="x"),
    )
    ctx = ValidationContext(
        verifier_input=VerifierInput(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            agent_id=uuid4(),
            planner_output=plan,
            current_state=SessionState.CALL_STARTED,
        )
    )
    ctx.registered_tool_slugs = {"appointment"}
    ctx.known_intents = {PlannerIntent.APPOINTMENT.value}
    violations = HallucinationDetector().validate(ctx)
    assert any("hallucinated_tool" in v for v in violations)


def test_hallucinated_order_data():
    plan = PlannerPlan(
        intent=PlannerIntent.GENERAL_QUESTION,
        confidence=0.8,
        reasoning=["x"],
        next_action="respond",
        action=PlannerAction.RESPOND,
        response="Your order #12345 has shipped.",
        plan=ExecutionPlan(goal="x"),
    )
    ctx = ValidationContext(
        verifier_input=VerifierInput(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            agent_id=uuid4(),
            planner_output=plan,
            working_memory={},
            current_state=SessionState.CALL_STARTED,
        )
    )
    ctx.known_intents = {PlannerIntent.GENERAL_QUESTION.value}
    violations = HallucinationDetector().validate(ctx)
    assert any("hallucinated_order_data" in v for v in violations)
