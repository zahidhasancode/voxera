"""Email sending tool."""

from typing import Any
from uuid import uuid4

from app.core.enums import ToolBuiltinSlug
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext


class EmailTool(BuiltinTool):
    def name(self) -> str:
        return "Send Email"

    def slug(self) -> str:
        return ToolBuiltinSlug.EMAIL

    def description(self) -> str:
        return "Send transactional or notification emails to customers."

    def permission_scope(self) -> str:
        return "communication"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string", "format": "email"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "template_id": {"type": "string"},
                "variables": {"type": "object"},
            },
            "required": ["to", "subject"],
            "additionalProperties": False,
        }

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        return {
            "message_id": str(uuid4()),
            "to": context.arguments["to"],
            "subject": context.arguments["subject"],
            "status": "queued",
            "provider": context.provider_config.get("provider", "smtp") if context.provider_config else "smtp",
        }
