"""Verifier prompt templates — safety-focused, not customer-facing."""

from app.verifier.schemas import VerifierInput


class VerifierPromptProvider:
    def system_prompt(self) -> str:
        return (
            "You are the VOXERA Enterprise Verifier Agent. "
            "You validate planner decisions. You never speak to customers. "
            "You never execute tools. You only approve, reject, or escalate."
        )

    def validation_prompt(self, verifier_input: VerifierInput) -> str:
        plan = verifier_input.planner_output
        return (
            f"Validate planner action={plan.action.value} intent={plan.intent.value} "
            f"confidence={plan.confidence}. Tenant policies apply."
        )

    def safety_prompt(self) -> str:
        return "Reject cross-tenant access, unknown tools, hallucinated data, and policy violations."
