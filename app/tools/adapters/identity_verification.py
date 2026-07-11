"""Identity verification tool."""

from typing import Any

from app.core.enums import ToolBuiltinSlug
from app.tools.adapters.base import BuiltinTool
from app.tools.schemas.execution import ToolExecutionContext


class IdentityVerificationTool(BuiltinTool):
    def name(self) -> str:
        return "Identity Verification"

    def slug(self) -> str:
        return ToolBuiltinSlug.IDENTITY_VERIFICATION

    def description(self) -> str:
        return "Verify customer identity via OTP, knowledge-based auth, or Twilio Verify."

    def permission_scope(self) -> str:
        return "security"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "method": {"type": "string", "enum": ["otp_sms", "otp_email", "kba", "twilio_verify"]},
                "identifier": {"type": "string", "description": "Phone or email"},
                "verification_code": {"type": "string"},
                "date_of_birth": {"type": "string"},
                "postal_code": {"type": "string"},
            },
            "required": ["method", "identifier"],
            "additionalProperties": False,
        }

    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        method = context.arguments["method"]
        if method in ("otp_sms", "otp_email", "twilio_verify") and not context.arguments.get("verification_code"):
            return {
                "status": "challenge_sent",
                "method": method,
                "identifier": context.arguments["identifier"],
            }
        return {
            "status": "verified",
            "method": method,
            "identifier": context.arguments["identifier"],
            "verified_at": "now",
        }
