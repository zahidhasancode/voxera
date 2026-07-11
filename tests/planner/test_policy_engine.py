"""Policy engine tests."""

from uuid import uuid4

import pytest

from app.core.enums import PlannerAction, PlannerIntent, PlannerRiskLevel, SessionState
from app.core.exceptions import PlannerPolicyViolationError
from app.planner.policies.policy_engine import PolicyEngine
from app.planner.schemas import ExecutionPlan, PlannerInput, PlannerPlan, ToolCallPlan


def _plan(**kwargs):
    defaults = dict(
        intent=PlannerIntent.APPOINTMENT,
        confidence=0.9,
        reasoning=["test"],
        next_action="book",
        action=PlannerAction.CALL_TOOL,
        tool_call=ToolCallPlan(tool_slug="appointment", arguments={"action": "book"}),
        response="Booking.",
        plan=ExecutionPlan(goal="book", risk_level=PlannerRiskLevel.LOW),
    )
    defaults.update(kwargs)
    return PlannerPlan(**defaults)


def _input(**policies):
    return PlannerInput(
        conversation_id=uuid4(),
        tenant_id=uuid4(),
        agent_id=uuid4(),
        current_state=SessionState.CALL_STARTED,
        tenant_policies=policies,
    )


def test_blocks_action():
    engine = PolicyEngine()
    with pytest.raises(PlannerPolicyViolationError):
        engine.evaluate(
            _input(blocked_actions=["call_tool"]),
            _plan(action=PlannerAction.CALL_TOOL),
        )


def test_blocks_tool():
    engine = PolicyEngine()
    with pytest.raises(PlannerPolicyViolationError):
        engine.evaluate(
            _input(blocked_tools=["appointment"]),
            _plan(),
        )


def test_allows_valid_plan():
    engine = PolicyEngine()
    plan, notes = engine.evaluate(_input(), _plan())
    assert plan.intent == PlannerIntent.APPOINTMENT
    assert isinstance(notes, list)
