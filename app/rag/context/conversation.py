"""Conversation context merger."""

from app.rag.interfaces.models import ConversationContext


class ConversationContextMerger:
    """Merges conversation history, summary, memory, and tool outputs."""

    def merge(self, context: ConversationContext) -> str:
        parts: list[str] = []

        if context.conversation_summary:
            parts.append(f"Conversation Summary:\n{context.conversation_summary.strip()}")

        if context.agent_memory:
            parts.append(f"Agent Memory:\n{context.agent_memory.strip()}")

        if context.current_turns:
            turn_lines = []
            for turn in context.current_turns[-10:]:
                turn_lines.append(f"{turn.role.upper()}: {turn.content.strip()}")
            parts.append("Recent Turns:\n" + "\n".join(turn_lines))

        if context.tool_outputs:
            tool_lines = []
            for output in context.tool_outputs[-5:]:
                tool_lines.append(f"[{output.tool_name}]: {output.output.strip()}")
            parts.append("Tool Outputs:\n" + "\n".join(tool_lines))

        return "\n\n".join(parts)

    def latest_user_query(self, context: ConversationContext, fallback: str) -> str:
        for turn in reversed(context.current_turns):
            if turn.role == "user":
                return turn.content.strip()
        return fallback
