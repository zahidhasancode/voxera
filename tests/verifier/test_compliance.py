"""Compliance engine tests."""

from uuid import uuid4

from app.core.enums import IdentityVerificationStatus, PlannerAction, PlannerIntent, SessionState
from app.planner.schemas import ExecutionPlan, PlannerPlan, ToolCallPlan
from app.verifier.compliance.engine import ComplianceEngine
from app.verifier.schemas import ValidationContext, VerifierInput


def test_gdpr_fails_without_consent():
    plan = PlannerPlan(
        intent=PlannerIntent.GENERAL_QUESTION,
        confidence=0.8,
        reasoning=["lookup"],
        next_action="lookup",
        action=PlannerAction.CALL_TOOL,
        tool_call=ToolCallPlan(tool_slug="crm_lookup", arguments={"value": "x"}),
        plan=ExecutionPlan(goal="lookup"),
    )
    ctx = ValidationContext(
        verifier_input=VerifierInput(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            agent_id=uuid4(),
            planner_output=plan,
            tenant_policies={"gdpr_enabled": True},
            working_memory={},
            identity_status=IdentityVerificationStatus.UNVERIFIED,
            current_state=SessionState.CALL_STARTED,
        )
    )
    violations = ComplianceEngine().evaluate(ctx, enabled_frameworks=["gdpr"])
    assert violations
