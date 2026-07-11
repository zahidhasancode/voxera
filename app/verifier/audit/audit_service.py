"""Verifier audit logging."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.enums import VerifierAuditStatus
from app.verifier.schemas import VerifierHistoryRead, VerifierInput, VerifierResult


class VerifierAuditService:
    def __init__(self, repository) -> None:
        self._repository = repository

    async def list_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ) -> list[VerifierHistoryRead]:
        return await self._repository.list_by_conversation(
            tenant_id, agent_id, conversation_id, limit=limit
        )

    async def log_verification(
        self,
        *,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        decision_id: UUID | None,
        verifier_input: VerifierInput,
        result: VerifierResult,
        validation_failures: list[str],
        policy_violations: list[str],
    ) -> VerifierHistoryRead:
        status = VerifierAuditStatus.APPROVED
        if not result.approved:
            status = VerifierAuditStatus.REJECTED
        elif result.outcome.value == "escalated":
            status = VerifierAuditStatus.ESCALATED
        elif policy_violations:
            status = VerifierAuditStatus.POLICY_VIOLATION
        elif not result.compliance_passed:
            status = VerifierAuditStatus.COMPLIANCE_FAILURE

        now = datetime.now(timezone.utc)
        return await self._repository.append(
            VerifierHistoryRead(
                id=uuid4(),
                tenant_id=tenant_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                decision_id=decision_id,
                status=status.value,
                planner_output=verifier_input.planner_output.model_dump(mode="json"),
                verifier_result=result.model_dump(mode="json"),
                validation_failures=validation_failures or None,
                policy_violations=policy_violations or None,
                risk_score=result.risk_score,
                identity_status=result.identity_status.value if result.identity_status else None,
                occurred_at=now,
                created_at=now,
                updated_at=now,
            )
        )
