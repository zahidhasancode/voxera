"""Structured (rule-based) planner model — provider-independent default."""

from app.planner.interfaces.planner_model import PlannerModel
from app.planner.prompts.templates import TemplatePromptProvider
from app.planner.reasoning.intent_engine import IntentEngine
from app.planner.reasoning.reasoning_loop import ReasoningLoop
from app.planner.schemas import OptimizedPlannerContext, PlannerInput, PlannerPlan


class StructuredPlannerModel(PlannerModel):
    """Production default planner — no external LLM dependency."""

    def __init__(
        self,
        *,
        intent_engine: IntentEngine | None = None,
        reasoning_loop: ReasoningLoop | None = None,
        prompts: TemplatePromptProvider | None = None,
    ) -> None:
        self._intent = intent_engine or IntentEngine()
        self._reasoning = reasoning_loop or ReasoningLoop(intent_engine=self._intent)
        self._prompts = prompts or TemplatePromptProvider()

    @property
    def provider_name(self) -> str:
        return "structured"

    async def health(self) -> dict:
        return {"status": "healthy", "provider": self.provider_name}

    def estimate_tokens(self, context: OptimizedPlannerContext) -> int:
        return context.token_estimate

    async def plan(self, context: OptimizedPlannerContext, planner_input: PlannerInput) -> PlannerPlan:
        _ = self._prompts.system_prompt(
            industry=planner_input.industry,
            language=planner_input.language,
        )
        _ = self._prompts.planning_prompt(context, planner_input)
        _ = self._prompts.safety_prompt(tenant_policies=planner_input.tenant_policies)
        _ = self._prompts.industry_prompt(planner_input.industry)
        _ = self._prompts.tenant_prompt(planner_input.tenant_policies)
        _ = self._prompts.language_prompt(planner_input.language)

        intent, confidence = self._intent.classify(
            context.current_user_message,
            language=planner_input.language,
        )
        return self._reasoning.evaluate(
            context,
            planner_input,
            intent=intent,
            confidence=confidence,
        )
