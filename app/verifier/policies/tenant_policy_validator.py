"""Tenant policy validation."""

from datetime import datetime, timezone

from app.core.enums import PlannerAction
from app.verifier.schemas import ValidationContext


class TenantPolicyValidator:
    def validate(self, ctx: ValidationContext) -> list[str]:
        violations: list[str] = []
        policies = ctx.verifier_input.tenant_policies or {}
        plan = ctx.verifier_input.planner_output

        blocked_actions = {a.lower() for a in policies.get("blocked_actions", [])}
        if plan.action.value in blocked_actions:
            violations.append(f"blocked_action:{plan.action.value}")

        blocked_tools = {t.lower() for t in policies.get("blocked_tools", [])}
        if plan.tool_call and plan.tool_call.tool_slug.lower() in blocked_tools:
            violations.append(f"blocked_tool:{plan.tool_call.tool_slug}")

        allowed_tools = policies.get("allowed_tools")
        if allowed_tools and plan.tool_call:
            allowed = {t.lower() for t in allowed_tools}
            if plan.tool_call.tool_slug.lower() not in allowed:
                violations.append(f"tool_not_allowed:{plan.tool_call.tool_slug}")

        allowed_languages = policies.get("allowed_languages")
        if allowed_languages and ctx.verifier_input.language not in allowed_languages:
            violations.append(f"language_not_allowed:{ctx.verifier_input.language}")

        start = policies.get("business_hours_start")
        end = policies.get("business_hours_end")
        if start and end and plan.action == PlannerAction.CALL_TOOL:
            now = datetime.now(timezone.utc).strftime("%H:%M")
            if not (start <= now <= end):
                violations.append("outside_business_hours")

        max_autonomy = policies.get("max_autonomy", "full")
        if max_autonomy == "restricted" and plan.action in (
            PlannerAction.CALL_TOOL,
            PlannerAction.ESCALATE,
            PlannerAction.TRANSFER_HUMAN,
        ):
            ctx.warnings.append("restricted_autonomy:action_requires_review")

        department = policies.get("department")
        if department and policies.get("department_restricted_tools"):
            restricted = policies["department_restricted_tools"].get(department, [])
            if plan.tool_call and plan.tool_call.tool_slug in restricted:
                violations.append(f"department_blocked_tool:{plan.tool_call.tool_slug}")

        return violations
