"""Human transfer / escalation tool."""

from typing import Any
from uuid import uuid4

from app.core.enums import ToolBuiltinSlug
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext


class HumanTransferTool(BuiltinTool):
    def name(self) -> str:
        return "Transfer to Human"

    def slug(self) -> str:
        return ToolBuiltinSlug.HUMAN_TRANSFER

    def description(self) -> str:
        return "Transfer the call or conversation to a human agent."

    def permission_scope(self) -> str:
        return "telephony"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "department": {"type": "string"},
                "reason": {"type": "string"},
                "priority": {"type": "string", "enum": ["normal", "high", "urgent"]},
                "warm_transfer": {"type": "boolean", "default": True},
            },
            "required": ["department", "reason"],
            "additionalProperties": False,
        }

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        return {
            "transfer_id": str(uuid4()),
            "department": context.arguments["department"],
            "reason": context.arguments["reason"],
            "status": "initiated",
            "warm_transfer": context.arguments.get("warm_transfer", True),
        }
