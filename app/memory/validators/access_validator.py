"""Memory access validation — security gate."""

from datetime import datetime, timezone
from uuid import UUID

from app.core.enums import ConversationStatus
from app.core.exceptions import CrossTenantMemoryError, MemoryAccessError, SessionExpiredError
from app.memory.schemas import SessionRead


class MemoryAccessValidator:
    """Validates tenant, agent, and conversation on every memory operation."""

    def validate_session_access(
        self,
        session: SessionRead,
        *,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        allow_completed: bool = False,
    ) -> None:
        violations: list[str] = []

        if session.id != conversation_id:
            violations.append("conversation_id_mismatch")
        if session.tenant_id != tenant_id:
            raise CrossTenantMemoryError(
                "Cross-tenant memory access denied",
                violations=["tenant_id_mismatch"],
            )
        if session.agent_id != agent_id:
            violations.append("agent_id_mismatch")

        if session.status == ConversationStatus.EXPIRED:
            raise SessionExpiredError("Session has expired", violations=["session_expired"])

        if session.expires_at and session.expires_at < datetime.now(timezone.utc):
            raise SessionExpiredError("Session TTL exceeded", violations=["session_ttl_exceeded"])

        if not allow_completed and session.status in (
            ConversationStatus.COMPLETED,
            ConversationStatus.ARCHIVED,
        ):
            raise SessionExpiredError(
                f"Session is {session.status.value}",
                violations=[f"session_{session.status.value}"],
            )

        if violations:
            raise MemoryAccessError("Memory access validation failed", violations=violations)

    def validate_turn_scope(
        self,
        *,
        tenant_id: UUID,
        agent_id: UUID,
        turn_tenant_id: UUID,
        turn_agent_id: UUID,
    ) -> None:
        if turn_tenant_id != tenant_id:
            raise CrossTenantMemoryError("Turn tenant mismatch")
        if turn_agent_id != agent_id:
            raise MemoryAccessError("Turn agent mismatch", violations=["turn_agent_mismatch"])

    @staticmethod
    def redact_sensitive(working_memory: dict[str, str], sensitive_keys: set[str]) -> dict[str, str]:
        return {k: ("[REDACTED]" if k in sensitive_keys else v) for k, v in working_memory.items()}
