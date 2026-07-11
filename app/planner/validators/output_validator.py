"""Planner output structural validation."""

from app.core.enums import PlannerAction
from app.core.exceptions import PlannerValidationError
from app.planner.schemas import PlannerPlan


class PlannerOutputValidator:
    def validate(self, plan: PlannerPlan) -> list[str]:
        violations: list[str] = []

        if not plan.reasoning:
            violations.append("reasoning: at least one step required")

        if plan.action == PlannerAction.CALL_TOOL and not plan.tool_call:
            violations.append("tool_call: required when action is call_tool")

        if plan.action == PlannerAction.RESPOND and not plan.response:
            violations.append("response: required when action is respond")

        if plan.action in (PlannerAction.ASK_CLARIFICATION, PlannerAction.RESPOND, PlannerAction.ESCALATE):
            if not plan.response and plan.action != PlannerAction.RETRIEVE:
                if plan.action != PlannerAction.CALL_TOOL:
                    pass  # escalate may have tool_call instead

        if plan.tool_call and not plan.tool_call.tool_slug:
            violations.append("tool_call.tool_slug: required")

        if violations:
            raise PlannerValidationError("Planner output validation failed", violations=violations)
        return violations
