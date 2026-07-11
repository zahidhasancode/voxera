"""Planner JSON schema validation."""

from app.core.enums import PlannerAction, PlannerIntent
from app.planner.schemas import PlannerPlan
from app.verifier.schemas import ValidationContext


class JsonSchemaValidator:
    """Validates planner output structure and known enums."""

    KNOWN_INTENTS = {i.value for i in PlannerIntent}
    KNOWN_ACTIONS = {a.value for a in PlannerAction}

    def validate(self, plan: PlannerPlan, ctx: ValidationContext) -> list[str]:
        violations: list[str] = []
        ctx.known_intents = self.KNOWN_INTENTS

        if plan.intent.value not in self.KNOWN_INTENTS:
            violations.append(f"unknown_intent:{plan.intent.value}")

        if plan.action.value not in self.KNOWN_ACTIONS:
            violations.append(f"unknown_action:{plan.action.value}")

        if not plan.reasoning:
            violations.append("missing_reasoning_steps")

        if plan.action == PlannerAction.CALL_TOOL and not plan.tool_call:
            violations.append("missing_tool_call_for_call_tool_action")

        if plan.tool_call and not plan.tool_call.tool_slug:
            violations.append("missing_tool_slug")

        if plan.confidence < 0 or plan.confidence > 1:
            violations.append("invalid_confidence_range")

        if plan.action == PlannerAction.RESPOND and not plan.response:
            violations.append("missing_response_for_respond_action")

        return violations
