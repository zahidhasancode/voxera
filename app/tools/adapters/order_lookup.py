"""Order lookup tool."""

from typing import Any

from app.core.enums import ToolBuiltinSlug
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext


class OrderLookupTool(BuiltinTool):
    def name(self) -> str:
        return "Order Lookup"

    def slug(self) -> str:
        return ToolBuiltinSlug.ORDER_LOOKUP

    def description(self) -> str:
        return "Look up order status (Shopify, WooCommerce, internal OMS)."

    def permission_scope(self) -> str:
        return "commerce"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "order_number": {"type": "string"},
                "customer_email": {"type": "string", "format": "email"},
                "commerce_provider": {
                    "type": "string",
                    "enum": ["shopify", "woocommerce", "internal"],
                },
            },
            "required": ["order_number"],
            "additionalProperties": False,
        }

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        provider = context.arguments.get("commerce_provider") or (
            context.provider_config.get("provider", "internal") if context.provider_config else "internal"
        )
        return {
            "order_number": context.arguments["order_number"],
            "status": "shipped",
            "provider": provider,
            "tracking_number": "TRK-000000",
            "estimated_delivery": None,
        }
