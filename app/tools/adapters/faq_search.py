"""FAQ search tool — delegates to knowledge base (no direct RAG engine call)."""

from typing import Any

from app.core.enums import ToolBuiltinSlug
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext


class FaqSearchTool(BuiltinTool):
    def name(self) -> str:
        return "FAQ Search"

    def slug(self) -> str:
        return ToolBuiltinSlug.FAQ_SEARCH

    def description(self) -> str:
        return "Search FAQ and knowledge base for answers."

    def permission_scope(self) -> str:
        return "knowledge"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3},
                "language": {"type": "string", "default": "en"},
            },
            "required": ["query"],
            "additionalProperties": False,
        }

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        return {
            "query": context.arguments["query"],
            "results": [],
            "note": "Attach RAG excerpts via Planner get_context(retrieved_knowledge=...) — FAQ tool returns structured placeholder",
            "language": context.arguments.get("language", "en"),
        }
