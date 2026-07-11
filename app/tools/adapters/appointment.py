"""Appointment booking tool."""

from typing import Any
from uuid import uuid4

from app.core.enums import ToolBuiltinSlug
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext


class AppointmentTool(BuiltinTool):
    def name(self) -> str:
        return "Book Appointment"

    def slug(self) -> str:
        return ToolBuiltinSlug.APPOINTMENT

    def description(self) -> str:
        return "Book, reschedule, or cancel customer appointments."

    def permission_scope(self) -> str:
        return "appointment"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["book", "reschedule", "cancel"]},
                "customer_name": {"type": "string"},
                "customer_email": {"type": "string", "format": "email"},
                "customer_phone": {"type": "string"},
                "datetime": {"type": "string", "description": "ISO-8601 datetime"},
                "appointment_id": {"type": "string"},
                "service_type": {"type": "string"},
                "timezone": {"type": "string", "default": "UTC"},
            },
            "required": ["action"],
            "additionalProperties": False,
        }

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        action = context.arguments["action"]
        appointment_id = context.arguments.get("appointment_id") or str(uuid4())
        return {
            "action": action,
            "appointment_id": appointment_id,
            "status": "confirmed" if action == "book" else action + "d",
            "provider": context.provider_config.get("provider", "internal") if context.provider_config else "internal",
            "scheduled_at": context.arguments.get("datetime"),
        }
