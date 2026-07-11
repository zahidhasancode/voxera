"""Default prompt templates loaded from template strings."""

from app.planner.prompts.provider import PromptProvider
from app.planner.schemas import OptimizedPlannerContext, PlannerInput


class TemplatePromptProvider(PromptProvider):
    def system_prompt(self, *, industry: str | None, language: str) -> str:
        return (
            "You are the VOXERA Enterprise Planner Agent. "
            "You THINK and PLAN only. You never execute tools, retrieve documents, "
            "or speak directly to customers without structured output. "
            f"Industry: {industry or 'general'}. Language: {language}."
        )

    def planning_prompt(self, context: OptimizedPlannerContext, planner_input: PlannerInput) -> str:
        tools = ", ".join(planner_input.available_tools[i].slug for i in range(min(len(planner_input.available_tools), 10)))
        return (
            f"User message: {context.current_user_message or ''}\n"
            f"State: {context.current_state.value}\n"
            f"Working memory keys: {list(context.working_memory.keys())}\n"
            f"Available tools: {tools}\n"
            "Return structured JSON plan with intent, action, reasoning, and response."
        )

    def safety_prompt(self, *, tenant_policies: dict) -> str:
        blocked = tenant_policies.get("blocked_actions", [])
        return f"Never plan actions that violate policy. Blocked: {blocked}"

    def industry_prompt(self, industry: str | None) -> str:
        if industry == "healthcare":
            return "HIPAA-aware planning. Verify identity before PHI access."
        if industry == "banking":
            return "Financial compliance. Never plan unauthorized transactions."
        return "Apply general enterprise safety standards."

    def tenant_prompt(self, tenant_policies: dict) -> str:
        autonomy = tenant_policies.get("max_autonomy", "standard")
        hours = tenant_policies.get("business_hours", "24/7")
        return f"Max autonomy: {autonomy}. Business hours: {hours}."

    def language_prompt(self, language: str) -> str:
        return f"Reason in structured form. Customer-facing response must be in language: {language}."
