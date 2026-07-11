"""Hallucination and unsupported claim detection."""

from app.core.enums import PlannerAction, PlannerIntent
from app.verifier.schemas import ValidationContext


class HallucinationDetector:
    def validate(self, ctx: ValidationContext) -> list[str]:
        violations: list[str] = []
        plan = ctx.verifier_input.planner_output
        wm = ctx.verifier_input.working_memory

        if plan.action == PlannerAction.CALL_TOOL and plan.tool_call:
            if plan.tool_call.tool_slug not in ctx.registered_tool_slugs and ctx.registered_tool_slugs:
                violations.append(f"hallucinated_tool:{plan.tool_call.tool_slug}")

        if plan.intent.value not in ctx.known_intents and ctx.known_intents:
            violations.append(f"hallucinated_intent:{plan.intent.value}")

        if plan.action == PlannerAction.RESPOND and plan.response:
            response_lower = plan.response.lower()
            if "policy states" in response_lower and not ctx.verifier_input.retrieved_knowledge:
                violations.append("hallucinated_policy_reference")
            if "your order #" in response_lower and "order_number" not in wm:
                violations.append("hallucinated_order_data")
            if "account balance" in response_lower and plan.intent != PlannerIntent.GENERAL_QUESTION:
                violations.append("hallucinated_financial_data")

        if plan.action == PlannerAction.RETRIEVE and ctx.verifier_input.retrieved_knowledge:
            ctx.warnings.append("retrieve_requested_but_knowledge_already_present")

        unsupported_doc_refs = ("confluence page", "sharepoint document", "internal wiki")
        if plan.response:
            for ref in unsupported_doc_refs:
                if ref in plan.response.lower() and not ctx.verifier_input.retrieved_knowledge:
                    violations.append(f"unsupported_document_reference:{ref}")

        return violations
