"""Policy and business rule validation tests."""

from uuid import uuid4

import pytest

from app.core.enums import PlannerAction, PlannerIntent, SessionState
from app.planner.schemas import ExecutionPlan, PlannerPlan, ToolCallPlan
from app.verifier.policies.business_rule_engine import BusinessRuleEngine
from app.verifier.policies.tenant_policy_validator import TenantPolicyValidator
from app.verifier.schemas import ValidationContext, VerifierInput


def _ctx(plan: PlannerPlan, policies: dict | None = None, wm: dict | None = None) -> ValidationContext:
    return ValidationContext(
        verifier_input=VerifierInput(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            agent_id=uuid4(),
            planner_output=plan,
            tenant_policies=policies or {},
            working_memory=wm or {},
            current_state=SessionState.CALL_STARTED,
        )
    )


def test_blocked_tool_rejected():
    plan = PlannerPlan(
        intent=PlannerIntent.APPOINTMENT,
        confidence=0.9,
        reasoning=["book"],
        next_action="book",
        action=PlannerAction.CALL_TOOL,
        tool_call=ToolCallPlan(tool_slug="appointment", arguments={}),
        plan=ExecutionPlan(goal="book"),
    )
    violations = TenantPolicyValidator().validate(
        _ctx(plan, policies={"blocked_tools": ["appointment"]})
    )
    assert any("blocked_tool" in v for v in violations)


def test_inactive_customer_rejected():
    plan = PlannerPlan(
        intent=PlannerIntent.ORDER_STATUS,
        confidence=0.85,
        reasoning=["lookup"],
        next_action="lookup",
        action=PlannerAction.CALL_TOOL,
        tool_call=ToolCallPlan(tool_slug="order_lookup", arguments={"order_number": "123"}),
        plan=ExecutionPlan(goal="lookup"),
    )
    violations = BusinessRuleEngine().validate(
        _ctx(
            plan,
            policies={"business_rules": [{"type": "customer_inactive"}]},
            wm={"customer_status": "inactive"},
        )
    )
    assert "customer_inactive" in violations
