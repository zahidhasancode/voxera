"""CRM lookup tool."""

from typing import Any

from app.core.enums import ToolBuiltinSlug
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext


class CrmLookupTool(BuiltinTool):
    def name(self) -> str:
        return "CRM Lookup"

    def slug(self) -> str:
        return ToolBuiltinSlug.CRM_LOOKUP

    def description(self) -> str:
        return "Look up customer records in CRM (Salesforce, HubSpot, Dynamics)."

    def permission_scope(self) -> str:
        return "crm"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "lookup_type": {"type": "string", "enum": ["email", "phone", "customer_id", "account_id"]},
                "value": {"type": "string"},
                "crm_provider": {
                    "type": "string",
                    "enum": ["salesforce", "hubspot", "dynamics", "internal"],
                },
            },
            "required": ["lookup_type", "value"],
            "additionalProperties": False,
        }

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        provider = context.arguments.get("crm_provider") or (
            context.provider_config.get("provider", "internal") if context.provider_config else "internal"
        )
        return {
            "found": True,
            "provider": provider,
            "lookup_type": context.arguments["lookup_type"],
            "record": {
                "customer_id": f"crm-{context.arguments['value'][:8]}",
                "name": "Customer Record",
                "status": "active",
            },
        }
