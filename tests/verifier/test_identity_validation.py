"""Identity validation tests."""

from uuid import uuid4

from app.core.enums import IdentityVerificationStatus, PlannerAction, PlannerIntent, SessionState
from app.planner.schemas import ExecutionPlan, PlannerPlan, ToolCallPlan
from app.verifier.validators.identity_validator import IdentityValidator
from app.verifier.schemas import ValidationContext, VerifierInput


def test_refund_requires_identity():
    plan = PlannerPlan(
        intent=PlannerIntent.REFUND,
        confidence=0.9,
        reasoning=["refund"],
        next_action="refund",
        action=PlannerAction.CALL_TOOL,
        tool_call=ToolCallPlan(tool_slug="crm_update", arguments={}),
        plan=ExecutionPlan(goal="refund"),
    )
    ctx = ValidationContext(
        verifier_input=VerifierInput(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            agent_id=uuid4(),
            planner_output=plan,
            working_memory={},
            identity_status=IdentityVerificationStatus.UNVERIFIED,
            current_state=SessionState.CALL_STARTED,
        )
    )
    violations = IdentityValidator().validate(ctx)
    assert "identity_verification_required" in violations


def test_verified_identity_passes():
    plan = PlannerPlan(
        intent=PlannerIntent.REFUND,
        confidence=0.9,
        reasoning=["refund"],
        next_action="refund",
        action=PlannerAction.CALL_TOOL,
        tool_call=ToolCallPlan(tool_slug="crm_update", arguments={}),
        plan=ExecutionPlan(goal="refund"),
    )
    ctx = ValidationContext(
        verifier_input=VerifierInput(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            agent_id=uuid4(),
            planner_output=plan,
            working_memory={"email": "a@b.com", "verification_status": "verified"},
            identity_status=IdentityVerificationStatus.VERIFIED,
            current_state=SessionState.IDENTITY_VERIFIED,
        )
    )
    violations = IdentityValidator().validate(ctx)
    assert "identity_verification_required" not in violations
