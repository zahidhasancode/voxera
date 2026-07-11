"""Conversation and memory consistency validation."""

from app.core.enums import PlannerAction, SessionState
from app.verifier.schemas import ValidationContext


class ConversationValidator:
    def validate(self, ctx: ValidationContext) -> list[str]:
        violations: list[str] = []
        inp = ctx.verifier_input
        plan = inp.planner_output
        wm = inp.working_memory

        if inp.current_state == SessionState.CALL_COMPLETED and plan.action != PlannerAction.END_CONVERSATION:
            violations.append("invalid_state:session_already_completed")

        email = wm.get("email")
        phone = wm.get("phone")
        if email and phone and "@" not in email:
            violations.append("conflicting_identity:invalid_email_format")

        if plan.action == PlannerAction.CALL_TOOL and inp.current_state == SessionState.IDENTITY_PENDING:
            if plan.tool_call and plan.tool_call.tool_slug not in ("identity_verification",):
                violations.append("invalid_state:tool_before_identity_verified")

        summary = inp.conversation_summary
        if summary and summary.pending_items:
            for item in summary.pending_items:
                if "verification" in item.lower() and plan.action == PlannerAction.CALL_TOOL:
                    if plan.tool_call and plan.tool_call.tool_slug not in ("identity_verification",):
                        ctx.warnings.append("pending_verification_item_exists")

        return violations
