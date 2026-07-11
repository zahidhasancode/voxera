"""Risk engine tests."""

from uuid import uuid4

from app.core.enums import (
    IdentityVerificationStatus,
    PlannerAction,
    PlannerIntent,
    SessionState,
    VerifierRiskLevel,
)
from app.planner.schemas import ExecutionPlan, PlannerPlan, ToolCallPlan
from app.verifier.policies.risk_engine import RiskEngine
from app.verifier.schemas import ValidationContext, VerifierInput


def _ctx(plan: PlannerPlan, **kwargs) -> ValidationContext:
    inp = VerifierInput(
        conversation_id=uuid4(),
        tenant_id=uuid4(),
        agent_id=uuid4(),
        planner_output=plan,
        current_state=SessionState.CALL_STARTED,
        **kwargs,
    )
    return ValidationContext(verifier_input=inp)


def test_low_risk_greeting_auto_approve():
    plan = PlannerPlan(
        intent=PlannerIntent.GREETING,
        confidence=0.92,
        reasoning=["greet"],
        next_action="respond",
        action=PlannerAction.RESPOND,
        response="Hello!",
        plan=ExecutionPlan(goal="greet"),
    )
    engine = RiskEngine()
    ctx = _ctx(plan)
    risk, _, _ = engine.assess(ctx)
    result = engine.apply_action_rules(risk, ctx)
    assert risk == VerifierRiskLevel.LOW
    assert result.approved is True


def test_high_risk_refund_requires_confirmation():
    plan = PlannerPlan(
        intent=PlannerIntent.REFUND,
        confidence=0.88,
        reasoning=["refund"],
        next_action="process_refund",
        action=PlannerAction.CALL_TOOL,
        tool_call=ToolCallPlan(tool_slug="crm_update", arguments={"amount": 100}),
        response="Processing refund.",
        plan=ExecutionPlan(goal="refund"),
    )
    engine = RiskEngine()
    ctx = _ctx(plan, identity_status=IdentityVerificationStatus.VERIFIED)
    risk, _, _ = engine.assess(ctx)
    result = engine.apply_action_rules(risk, ctx)
    assert risk == VerifierRiskLevel.HIGH
    assert result.requires_confirmation is True


def test_violations_reject():
    plan = PlannerPlan(
        intent=PlannerIntent.APPOINTMENT,
        confidence=0.9,
        reasoning=["book"],
        next_action="book",
        action=PlannerAction.CALL_TOOL,
        tool_call=ToolCallPlan(tool_slug="appointment", arguments={"action": "book"}),
        plan=ExecutionPlan(goal="book"),
    )
    engine = RiskEngine()
    ctx = _ctx(plan)
    ctx.violations.append("blocked_tool:appointment")
    risk, _, _ = engine.assess(ctx)
    result = engine.apply_action_rules(risk, ctx)
    assert result.approved is False
