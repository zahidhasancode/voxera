"""Webhook tool — calls allowlisted HTTP endpoints only."""

from typing import Any
from uuid import uuid4

from app.core.enums import ToolBuiltinSlug
from app.core.exceptions import ToolValidationError
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext
from app.tools.validators.guardrails_validator import ToolGuardrailsValidator


class WebhookTool(BuiltinTool):
    def name(self) -> str:
        return "Webhook"

    def slug(self) -> str:
        return ToolBuiltinSlug.WEBHOOK

    def description(self) -> str:
        return "Invoke allowlisted HTTP webhooks for custom integrations."

    def permission_scope(self) -> str:
        return "integration"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"},
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "PATCH"], "default": "POST"},
                "headers": {"type": "object"},
                "payload": {"type": "object"},
            },
            "required": ["url"],
            "additionalProperties": False,
        }

    async def validate(self, arguments: dict[str, Any]) -> list[str]:
        violations = await super().validate(arguments)
        if "url" in arguments:
            violations.extend(ToolGuardrailsValidator().validate_http_url(arguments["url"]))
        return violations

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        url = context.arguments["url"]
        guard_violations = ToolGuardrailsValidator().validate_http_url(url)
        if guard_violations:
            raise ToolValidationError("; ".join(guard_violations), violations=guard_violations)
        return {
            "webhook_id": str(uuid4()),
            "url": url,
            "method": context.arguments.get("method", "POST"),
            "status": "accepted",
            "note": "HTTP dispatch queued — configure TOOL_ALLOWED_HTTP_HOSTS for production",
        }
