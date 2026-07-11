"""Tenant policy enforcement for planner decisions."""

from datetime import datetime, timezone

from app.core.enums import PlannerAction, PlannerIntent, PlannerRiskLevel
from app.core.exceptions import PlannerPolicyViolationError
from app.planner.schemas import PlannerInput, PlannerPlan


class PolicyEngine:
    """Evaluates tenant policies, compliance, business hours, and tool allowlists."""

    def evaluate(self, planner_input: PlannerInput, plan: PlannerPlan) -> tuple[PlannerPlan, list[str]]:
        policies = planner_input.tenant_policies or {}
        notes: list[str] = []

        blocked_actions = {a.lower() for a in policies.get("blocked_actions", [])}
        if plan.action.value in blocked_actions:
            raise PlannerPolicyViolationError(
                f"Action {plan.action.value} blocked by tenant policy",
                violations=[f"blocked_action:{plan.action.value}"],
            )

        blocked_tools = {t.lower() for t in policies.get("blocked_tools", [])}
        if plan.tool_call and plan.tool_call.tool_slug.lower() in blocked_tools:
            raise PlannerPolicyViolationError(
                f"Tool {plan.tool_call.tool_slug} blocked by tenant policy",
                violations=[f"blocked_tool:{plan.tool_call.tool_slug}"],
            )

        allowed_tools = policies.get("allowed_tools")
        if allowed_tools and plan.tool_call:
            allowed = {t.lower() for t in allowed_tools}
            if plan.tool_call.tool_slug.lower() not in allowed:
                raise PlannerPolicyViolationError(
                    f"Tool {plan.tool_call.tool_slug} not in allowed list",
                    violations=[f"tool_not_allowed:{plan.tool_call.tool_slug}"],
                )

        max_autonomy = policies.get("max_autonomy", "full")
        if max_autonomy == "restricted" and plan.action in (
            PlannerAction.CALL_TOOL,
            PlannerAction.ESCALATE,
            PlannerAction.TRANSFER_HUMAN,
        ):
            if plan.plan.risk_level in (PlannerRiskLevel.HIGH, PlannerRiskLevel.CRITICAL):
                notes.append("restricted_autonomy: high-risk action flagged")

        if not self._within_business_hours(policies):
            if plan.action == PlannerAction.CALL_TOOL and plan.intent not in (
                PlannerIntent.EMERGENCY,
            ):
                notes.append("outside_business_hours: tool call may be deferred")

        escalation_rules = policies.get("escalation_rules", {})
        if plan.intent == PlannerIntent.COMPLAINT and escalation_rules.get("auto_escalate_complaints"):
            if plan.action != PlannerAction.TRANSFER_HUMAN:
                notes.append("escalation_rule: complaint auto-escalation recommended")

        plan.policy_notes = notes
        return plan, notes

    def _within_business_hours(self, policies: dict) -> bool:
        start = policies.get("business_hours_start")
        end = policies.get("business_hours_end")
        if not start or not end:
            return True
        now = datetime.now(timezone.utc).strftime("%H:%M")
        return start <= now <= end
