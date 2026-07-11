"""Calendar event tool."""

from typing import Any
from uuid import uuid4

from app.core.enums import ToolBuiltinSlug
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext


class CalendarTool(BuiltinTool):
    def name(self) -> str:
        return "Calendar Event"

    def slug(self) -> str:
        return ToolBuiltinSlug.CALENDAR

    def description(self) -> str:
        return "Create or update calendar events (Google Calendar, Outlook)."

    def permission_scope(self) -> str:
        return "calendar"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["create", "update", "delete"]},
                "title": {"type": "string"},
                "start_time": {"type": "string"},
                "end_time": {"type": "string"},
                "attendees": {"type": "array", "items": {"type": "string", "format": "email"}},
                "event_id": {"type": "string"},
                "calendar_provider": {
                    "type": "string",
                    "enum": ["google", "outlook", "internal"],
                },
            },
            "required": ["action", "title"],
            "additionalProperties": False,
        }

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        event_id = context.arguments.get("event_id") or str(uuid4())
        provider = context.arguments.get("calendar_provider") or (
            context.provider_config.get("provider", "internal") if context.provider_config else "internal"
        )
        return {
            "event_id": event_id,
            "action": context.arguments["action"],
            "provider": provider,
            "status": "scheduled",
            "title": context.arguments["title"],
        }
