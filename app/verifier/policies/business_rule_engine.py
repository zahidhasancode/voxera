"""Configurable per-tenant business rules."""

from app.core.config import settings
from app.core.enums import PlannerAction, PlannerIntent
from app.verifier.schemas import ValidationContext


class BusinessRuleEngine:
    """Evaluates tenant-configurable business rules."""

    def validate(self, ctx: ValidationContext) -> list[str]:
        violations: list[str] = []
        rules = ctx.verifier_input.tenant_policies.get("business_rules", [])
        plan = ctx.verifier_input.planner_output
        wm = ctx.verifier_input.working_memory

        for rule in rules:
            rule_type = rule.get("type")
            if rule_type == "refund_threshold" and plan.intent == PlannerIntent.REFUND:
                amount = float(wm.get("refund_amount", plan.tool_call.arguments.get("amount", 0) if plan.tool_call else 0) or 0)
                threshold = float(rule.get("threshold", settings.VERIFIER_REFUND_HUMAN_THRESHOLD_USD))
                if amount > threshold:
                    ctx.warnings.append(f"refund_exceeds_threshold:{amount}>{threshold}")
                    ctx.risk_factors.append("high_value_refund")

            if rule_type == "customer_inactive" and wm.get("customer_status") == "inactive":
                violations.append("customer_inactive")

            if rule_type == "missing_consent" and rule.get("required_for") == plan.intent.value:
                if wm.get("consent_given") != "true":
                    violations.append("missing_consent")

            if rule_type == "appointment_after_hours" and plan.tool_call and plan.tool_call.tool_slug == "appointment":
                if rule.get("reject_outside_hours") and "outside_business_hours" in ctx.violations:
                    violations.append("appointment_after_working_hours")

        if plan.intent == PlannerIntent.REFUND:
            amount = float(wm.get("refund_amount", 0) or 0)
            if amount > settings.VERIFIER_REFUND_HUMAN_THRESHOLD_USD:
                ctx.risk_factors.append("refund_over_default_threshold")

        if plan.action == PlannerAction.CALL_TOOL and plan.tool_call and plan.tool_call.tool_slug == "webhook":
            ctx.risk_factors.append("webhook_invocation")

        return violations
