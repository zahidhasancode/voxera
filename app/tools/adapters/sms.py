"""SMS sending tool."""

from typing import Any
from uuid import uuid4

from app.core.enums import ToolBuiltinSlug
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext


class SmsTool(BuiltinTool):
    def name(self) -> str:
        return "Send SMS"

    def slug(self) -> str:
        return ToolBuiltinSlug.SMS

    def description(self) -> str:
        return "Send SMS notifications to customers."

    def permission_scope(self) -> str:
        return "communication"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "E.164 phone number"},
                "message": {"type": "string", "maxLength": 1600},
                "template_id": {"type": "string"},
            },
            "required": ["to", "message"],
            "additionalProperties": False,
        }

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        return {
            "message_sid": str(uuid4()),
            "to": context.arguments["to"],
            "status": "queued",
            "provider": context.provider_config.get("provider", "twilio") if context.provider_config else "twilio",
        }
