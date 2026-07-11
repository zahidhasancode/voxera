"""Context optimization — minimal token footprint for planning."""

from app.core.config import settings
from app.planner.schemas import OptimizedPlannerContext, PlannerInput


class ContextOptimizer:
    """Strips unnecessary context before model planning."""

    def optimize(self, planner_input: PlannerInput) -> OptimizedPlannerContext:
        knowledge = planner_input.retrieved_knowledge[:8]
        tool_results = planner_input.tool_results[-5:]
        working_memory = dict(list(planner_input.working_memory.items())[:20])

        summary = planner_input.conversation_summary
        if summary and summary.summary_text and len(summary.summary_text) > 2000:
            summary = summary.model_copy(
                update={"summary_text": summary.summary_text[:2000] + "..."}
            )

        message = planner_input.current_user_message
        if message and len(message) > 4000:
            message = message[:4000]

        ctx = OptimizedPlannerContext(
            current_user_message=message,
            conversation_summary=summary,
            working_memory=working_memory,
            retrieved_knowledge=knowledge,
            tool_results=tool_results,
            current_state=planner_input.current_state,
            language=planner_input.language,
            available_tool_slugs=[t.slug for t in planner_input.available_tools if t.enabled],
        )
        ctx.token_estimate = self._estimate_tokens(ctx)
        if ctx.token_estimate > settings.PLANNER_MAX_CONTEXT_TOKENS:
            ctx.retrieved_knowledge = ctx.retrieved_knowledge[:3]
            ctx.tool_results = ctx.tool_results[-2:]
            ctx.token_estimate = self._estimate_tokens(ctx)
        return ctx

    def _estimate_tokens(self, context: OptimizedPlannerContext) -> int:
        parts = [
            context.current_user_message or "",
            context.conversation_summary.summary_text if context.conversation_summary else "",
            str(context.working_memory),
            " ".join(context.retrieved_knowledge),
            str(context.tool_results),
        ]
        return sum(max(1, len(p) // 4) for p in parts)
