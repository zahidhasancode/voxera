"""Retrieved knowledge validation."""

from app.core.config import settings
from app.core.enums import PlannerAction
from app.verifier.schemas import ValidationContext


class KnowledgeValidator:
    def validate(self, ctx: ValidationContext) -> list[str]:
        violations: list[str] = []
        inp = ctx.verifier_input
        plan = inp.planner_output

        if plan.action == PlannerAction.RESPOND and plan.intent.value == "general_question":
            if not inp.retrieved_knowledge and "?" in (inp.planner_output.response or ""):
                ctx.warnings.append("response_without_retrieved_knowledge")

        for meta in inp.knowledge_metadata:
            tenant_id = meta.get("tenant_id")
            if tenant_id and str(tenant_id) != str(inp.tenant_id):
                violations.append("cross_tenant_knowledge_reference")

            if meta.get("status") == "expired":
                violations.append("expired_policy_document")

            similarity = meta.get("similarity")
            if similarity is not None and similarity < settings.VERIFIER_KNOWLEDGE_MIN_SIMILARITY:
                violations.append(f"low_similarity_knowledge:{similarity}")

            if meta.get("active") is False:
                violations.append("inactive_document_reference")

        return violations
