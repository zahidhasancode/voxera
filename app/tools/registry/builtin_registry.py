"""Built-in tool plugin registry."""

from app.core.config import settings
from app.tools.adapters.appointment import AppointmentTool
from app.tools.adapters.calendar import CalendarTool
from app.tools.adapters.crm_lookup import CrmLookupTool
from app.tools.adapters.crm_update import CrmUpdateTool
from app.tools.adapters.email import EmailTool
from app.tools.adapters.faq_search import FaqSearchTool
from app.tools.adapters.human_transfer import HumanTransferTool
from app.tools.adapters.identity_verification import IdentityVerificationTool
from app.tools.adapters.order_lookup import OrderLookupTool
from app.tools.adapters.sms import SmsTool
from app.tools.adapters.ticket_creation import TicketCreationTool
from app.tools.adapters.webhook import WebhookTool
from app.tools.interfaces.tool import Tool


def build_builtin_tools() -> dict[str, Tool]:
    if not settings.TOOL_ENABLE_BUILTIN_TOOLS:
        return {}
    tools: list[Tool] = [
        AppointmentTool(),
        CalendarTool(),
        EmailTool(),
        SmsTool(),
        CrmLookupTool(),
        CrmUpdateTool(),
        OrderLookupTool(),
        TicketCreationTool(),
        FaqSearchTool(),
        HumanTransferTool(),
        IdentityVerificationTool(),
        WebhookTool(),
    ]
    return {tool.slug(): tool for tool in tools}
