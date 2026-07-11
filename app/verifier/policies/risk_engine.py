"""Risk assessment engine."""

from app.core.config import settings
from app.core.enums import PlannerAction, PlannerIntent, VerifierRiskLevel
from app.verifier.schemas import ValidationContext, VerifierResult, VerifierOutcome


INTENT_RISK = {
    PlannerIntent.GREETING: VerifierRiskLevel.LOW,
    PlannerIntent.GENERAL_QUESTION: VerifierRiskLevel.LOW,
    PlannerIntent.APPOINTMENT: VerifierRiskLevel.LOW,
    PlannerIntent.ORDER_STATUS: VerifierRiskLevel.LOW,
    PlannerIntent.TECHNICAL_ISSUE: VerifierRiskLevel.MEDIUM,
    PlannerIntent.COMPLAINT: VerifierRiskLevel.MEDIUM,
    PlannerIntent.CANCEL_SUBSCRIPTION: VerifierRiskLevel.HIGH,
    PlannerIntent.REFUND: VerifierRiskLevel.HIGH,
    PlannerIntent.EMERGENCY: VerifierRiskLevel.CRITICAL,
    PlannerIntent.IDENTITY_VERIFICATION: VerifierRiskLevel.MEDIUM,
    PlannerIntent.UNKNOWN: VerifierRiskLevel.MEDIUM,
}

TOOL_RISK = {
    "appointment": VerifierRiskLevel.LOW,
    "calendar": VerifierRiskLevel.LOW,
    "email": VerifierRiskLevel.LOW,
    "sms": VerifierRiskLevel.LOW,
    "faq_search": VerifierRiskLevel.LOW,
    "order_lookup": VerifierRiskLevel.LOW,
    "ticket_creation": VerifierRiskLevel.MEDIUM,
    "crm_lookup": VerifierRiskLevel.MEDIUM,
    "crm_update": VerifierRiskLevel.MEDIUM,
    "identity_verification": VerifierRiskLevel.MEDIUM,
    "human_transfer": VerifierRiskLevel.HIGH,
    "webhook": VerifierRiskLevel.HIGH,
}


class RiskEngine:
    """Computes risk level and approval requirements."""

    def assess(self, ctx: ValidationContext) -> tuple[VerifierRiskLevel, float, list[str]]:
        plan = ctx.verifier_input.planner_output
        factors = list(ctx.risk_factors)

        base = INTENT_RISK.get(plan.intent, VerifierRiskLevel.MEDIUM)
        if plan.tool_call:
            tool_risk = TOOL_RISK.get(plan.tool_call.tool_slug, VerifierRiskLevel.MEDIUM)
            base = self._max_risk(base, tool_risk)
            factors.append(f"tool:{plan.tool_call.tool_slug}")

        if plan.plan.risk_level.value in ("high", "critical"):
            base = self._max_risk(base, VerifierRiskLevel(plan.plan.risk_level.value))

        if plan.confidence < settings.VERIFIER_MIN_CONFIDENCE:
            factors.append("low_planner_confidence")
            base = self._max_risk(base, VerifierRiskLevel.MEDIUM)

        if ctx.violations:
            base = self._max_risk(base, VerifierRiskLevel.HIGH)

        score_map = {
            VerifierRiskLevel.LOW: 0.2,
            VerifierRiskLevel.MEDIUM: 0.5,
            VerifierRiskLevel.HIGH: 0.75,
            VerifierRiskLevel.CRITICAL: 1.0,
        }
        score = score_map[base] + (0.05 * len(factors))
        score = min(score, 1.0)

        ctx.risk_level = base
        ctx.risk_score = score
        return base, score, factors

    def apply_action_rules(self, risk: VerifierRiskLevel, ctx: ValidationContext) -> VerifierResult:
        plan = ctx.verifier_input.planner_output
        violations = ctx.violations

        if violations:
            return VerifierResult(
                approved=False,
                outcome=VerifierOutcome.REJECTED,
                risk=risk,
                requires_confirmation=False,
                requires_human=False,
                reason="; ".join(violations[:5]),
                warnings=ctx.warnings,
                violations=violations,
                identity_status=ctx.identity_status,
                compliance_passed=ctx.compliance_passed,
                risk_score=ctx.risk_score,
            )

        if not ctx.compliance_passed:
            return VerifierResult(
                approved=False,
                outcome=VerifierOutcome.REJECTED,
                risk=risk,
                reason="Compliance check failed",
                warnings=ctx.warnings,
                violations=ctx.compliance_findings,
                identity_status=ctx.identity_status,
                compliance_passed=False,
                risk_score=ctx.risk_score,
            )

        if risk == VerifierRiskLevel.CRITICAL or plan.intent == PlannerIntent.EMERGENCY:
            return VerifierResult(
                approved=True,
                outcome=VerifierOutcome.ESCALATED,
                risk=risk,
                requires_confirmation=False,
                requires_human=True,
                warnings=ctx.warnings,
                identity_status=ctx.identity_status,
                compliance_passed=True,
                risk_score=ctx.risk_score,
            )

        if risk == VerifierRiskLevel.HIGH:
            return VerifierResult(
                approved=True,
                outcome=VerifierOutcome.REQUIRES_CONFIRMATION,
                risk=risk,
                requires_confirmation=True,
                requires_human=ctx.identity_status.value != "verified",
                warnings=ctx.warnings + (["identity_verification_recommended"] if ctx.identity_status.value != "verified" else []),
                corrected_tool_arguments=self._corrected_args(ctx),
                identity_status=ctx.identity_status,
                compliance_passed=True,
                risk_score=ctx.risk_score,
            )

        if risk == VerifierRiskLevel.MEDIUM:
            return VerifierResult(
                approved=True,
                outcome=VerifierOutcome.REQUIRES_CONFIRMATION if plan.action == PlannerAction.CALL_TOOL else VerifierOutcome.APPROVED,
                risk=risk,
                requires_confirmation=plan.action == PlannerAction.CALL_TOOL,
                requires_human=False,
                warnings=ctx.warnings,
                corrected_tool_arguments=self._corrected_args(ctx),
                identity_status=ctx.identity_status,
                compliance_passed=True,
                risk_score=ctx.risk_score,
            )

        auto = settings.VERIFIER_AUTO_APPROVE_LOW_RISK
        return VerifierResult(
            approved=auto,
            outcome=VerifierOutcome.APPROVED if auto else VerifierOutcome.REQUIRES_CONFIRMATION,
            risk=risk,
            requires_confirmation=not auto,
            requires_human=False,
            warnings=ctx.warnings,
            corrected_tool_arguments=self._corrected_args(ctx),
            identity_status=ctx.identity_status,
            compliance_passed=True,
            risk_score=ctx.risk_score,
        )

    def _corrected_args(self, ctx: ValidationContext) -> dict | None:
        plan = ctx.verifier_input.planner_output
        if not plan.tool_call:
            return None
        args = dict(plan.tool_call.arguments)
        wm = ctx.verifier_input.working_memory
        if "email" not in args and wm.get("email"):
            args["email"] = wm["email"]
        if "customer_email" not in args and wm.get("email"):
            args["customer_email"] = wm["email"]
        if "phone" not in args and wm.get("phone"):
            args["phone"] = wm["phone"]
        if "order_number" not in args and wm.get("order_number"):
            args["order_number"] = wm["order_number"]
        ctx.corrected_arguments = args
        return args if args != plan.tool_call.arguments else None

    def _max_risk(self, a: VerifierRiskLevel, b: VerifierRiskLevel) -> VerifierRiskLevel:
        order = [VerifierRiskLevel.LOW, VerifierRiskLevel.MEDIUM, VerifierRiskLevel.HIGH, VerifierRiskLevel.CRITICAL]
        return order[max(order.index(a), order.index(b))]
