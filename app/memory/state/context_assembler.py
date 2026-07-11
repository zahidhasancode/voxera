"""Planner context assembly."""

from app.core.enums import SessionState
from app.memory.schemas import PlannerContext, StructuredSummary, ToolExecutionRead, TurnRead


class PlannerContextAssembler:
    """Assembles unified PlannerContext from memory components."""

    def assemble(
        self,
        *,
        conversation_id,
        tenant_id,
        agent_id,
        current_state: SessionState,
        language: str,
        current_user_message: str | None,
        summary: StructuredSummary | None,
        working_memory: dict[str, str],
        tool_results: list[ToolExecutionRead],
        recent_turns: list[TurnRead],
        retrieved_knowledge: list[str] | None = None,
        agent_configuration: dict | None = None,
        tenant_policies: dict | None = None,
    ) -> PlannerContext:
        token_parts = [len(current_user_message or "") // 4]
        if summary:
            token_parts.append(summary.token_estimate)
        token_parts.append(sum(len(v) // 4 for v in working_memory.values()))
        token_parts.append(sum(len(t.message) // 4 for t in recent_turns[-6:]))
        token_parts.append(sum(len(t.result or "") // 4 for t in tool_results))

        return PlannerContext(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            current_user_message=current_user_message,
            conversation_summary=summary,
            working_memory=working_memory,
            retrieved_knowledge=retrieved_knowledge or [],
            tool_results=tool_results,
            agent_configuration=agent_configuration or {},
            tenant_policies=tenant_policies or {},
            current_state=current_state,
            language=language,
            recent_turns=recent_turns[-6:],
            token_estimate=sum(token_parts),
        )
