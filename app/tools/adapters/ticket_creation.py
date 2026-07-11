"""Support ticket creation tool."""

from typing import Any
from uuid import uuid4

from app.core.enums import ToolBuiltinSlug
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext


class TicketCreationTool(BuiltinTool):
    def name(self) -> str:
        return "Create Support Ticket"

    def slug(self) -> str:
        return ToolBuiltinSlug.TICKET_CREATION

    def description(self) -> str:
        return "Create support tickets (Zendesk, Freshdesk, internal)."

    def permission_scope(self) -> str:
        return "support"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"]},
                "customer_email": {"type": "string", "format": "email"},
                "ticket_provider": {
                    "type": "string",
                    "enum": ["zendesk", "freshdesk", "internal"],
                },
            },
            "required": ["subject", "description"],
            "additionalProperties": False,
        }

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        provider = context.arguments.get("ticket_provider") or (
            context.provider_config.get("provider", "internal") if context.provider_config else "internal"
        )
        return {
            "ticket_id": str(uuid4()),
            "subject": context.arguments["subject"],
            "priority": context.arguments.get("priority", "normal"),
            "provider": provider,
            "status": "open",
        }
