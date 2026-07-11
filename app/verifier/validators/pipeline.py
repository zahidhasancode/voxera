"""Validation pipeline orchestrator."""

from app.core.enums import PlannerIntent
from app.verifier.compliance.engine import ComplianceEngine
from app.verifier.policies.business_rule_engine import BusinessRuleEngine
from app.verifier.policies.risk_engine import RiskEngine
from app.verifier.policies.tenant_policy_validator import TenantPolicyValidator
from app.verifier.schemas import ValidationContext, VerifierInput, VerifierResult
from app.verifier.validators.conversation_validator import ConversationValidator
from app.verifier.validators.hallucination_detector import HallucinationDetector
from app.verifier.validators.identity_validator import IdentityValidator
from app.verifier.validators.json_validator import JsonSchemaValidator
from app.verifier.validators.knowledge_validator import KnowledgeValidator
from app.verifier.validators.tool_validator import ToolValidator


class ValidationPipeline:
    """Runs all validation stages in mandatory order."""

    def __init__(
        self,
        *,
        json_validator: JsonSchemaValidator | None = None,
        tenant_policy: TenantPolicyValidator | None = None,
        tool_validator: ToolValidator | None = None,
        identity_validator: IdentityValidator | None = None,
        conversation_validator: ConversationValidator | None = None,
        knowledge_validator: KnowledgeValidator | None = None,
        hallucination_detector: HallucinationDetector | None = None,
        business_rules: BusinessRuleEngine | None = None,
        compliance_engine: ComplianceEngine | None = None,
        risk_engine: RiskEngine | None = None,
    ) -> None:
        self._json = json_validator or JsonSchemaValidator()
        self._tenant = tenant_policy or TenantPolicyValidator()
        self._tool = tool_validator or ToolValidator()
        self._identity = identity_validator or IdentityValidator()
        self._conversation = conversation_validator or ConversationValidator()
        self._knowledge = knowledge_validator or KnowledgeValidator()
        self._hallucination = hallucination_detector or HallucinationDetector()
        self._business = business_rules or BusinessRuleEngine()
        self._compliance = compliance_engine or ComplianceEngine()
        self._risk = risk_engine or RiskEngine()

    def run(self, verifier_input: VerifierInput) -> tuple[ValidationContext, VerifierResult]:
        ctx = ValidationContext(verifier_input=verifier_input)
        ctx.known_intents = self._json.KNOWN_INTENTS

        stages = (
            self._json.validate(verifier_input.planner_output, ctx),
            self._tenant.validate(ctx),
            self._tool.validate(ctx),
            self._identity.validate(ctx),
            self._conversation.validate(ctx),
            self._knowledge.validate(ctx),
            self._hallucination.validate(ctx),
            self._business.validate(ctx),
        )
        for stage_violations in stages:
            ctx.violations.extend(stage_violations)

        compliance_frameworks = verifier_input.tenant_policies.get("compliance_frameworks")
        compliance_violations = self._compliance.evaluate(ctx, enabled_frameworks=compliance_frameworks)
        ctx.violations.extend(compliance_violations)

        risk, score, factors = self._risk.assess(ctx)
        ctx.risk_factors.extend(factors)

        if verifier_input.planner_output.intent == PlannerIntent.EMERGENCY:
            ctx.risk_level = risk
            ctx.risk_score = max(score, 0.95)

        result = self._risk.apply_action_rules(ctx.risk_level, ctx)
        return ctx, result
