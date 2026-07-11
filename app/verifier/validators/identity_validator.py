"""Identity verification gate for sensitive actions."""

from app.core.enums import IdentityVerificationStatus, PlannerAction, PlannerIntent
from app.verifier.schemas import ValidationContext


SENSITIVE_INTENTS = {
    PlannerIntent.REFUND,
    PlannerIntent.CANCEL_SUBSCRIPTION,
}
SENSITIVE_TOOLS = {
    "crm_update",
    "webhook",
    "human_transfer",
}


class IdentityValidator:
    def validate(self, ctx: ValidationContext) -> list[str]:
        violations: list[str] = []
        plan = ctx.verifier_input.planner_output
        wm = ctx.verifier_input.working_memory

        status = IdentityVerificationStatus.UNVERIFIED
        ver_status = wm.get("verification_status", "").lower()
        if ver_status == "verified":
            status = IdentityVerificationStatus.VERIFIED
        elif ver_status == "pending":
            status = IdentityVerificationStatus.PENDING
        elif ver_status == "failed":
            status = IdentityVerificationStatus.FAILED

        ctx.identity_status = status

        sensitive = (
            plan.intent in SENSITIVE_INTENTS
            or (plan.tool_call and plan.tool_call.tool_slug in SENSITIVE_TOOLS)
            or plan.action in (PlannerAction.ESCALATE, PlannerAction.TRANSFER_HUMAN)
        )

        if sensitive and status != IdentityVerificationStatus.VERIFIED:
            if plan.intent == PlannerIntent.REFUND or (plan.tool_call and plan.tool_call.tool_slug == "crm_update"):
                violations.append("identity_verification_required")
            elif plan.action == PlannerAction.TRANSFER_HUMAN and plan.intent != PlannerIntent.EMERGENCY:
                ctx.warnings.append("human_transfer_without_full_verification")

        if plan.tool_call and plan.tool_call.tool_slug == "identity_verification":
            return violations

        if sensitive and not wm.get("email") and not wm.get("phone") and not wm.get("customer_name"):
            violations.append("missing_customer_identity_fields")

        return violations
