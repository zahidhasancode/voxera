"""CRM update tool."""

from typing import Any

from app.core.enums import ToolBuiltinSlug
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext


class CrmUpdateTool(BuiltinTool):
    def name(self) -> str:
        return "CRM Update"

    def slug(self) -> str:
        return ToolBuiltinSlug.CRM_UPDATE

    def description(self) -> str:
        return "Update customer records in CRM systems."

    def permission_scope(self) -> str:
        return "crm"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "fields": {"type": "object"},
                "crm_provider": {
                    "type": "string",
                    "enum": ["salesforce", "hubspot", "dynamics", "internal"],
                },
            },
            "required": ["customer_id", "fields"],
            "additionalProperties": False,
        }

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        provider = context.arguments.get("crm_provider") or (
            context.provider_config.get("provider", "internal") if context.provider_config else "internal"
        )
        return {
            "customer_id": context.arguments["customer_id"],
            "updated_fields": list(context.arguments["fields"].keys()),
            "provider": provider,
            "status": "updated",
        }
