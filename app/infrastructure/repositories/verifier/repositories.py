"""SQLAlchemy verifier repositories."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.verifier import (
    ComplianceCheckModel,
    PolicyViolationModel,
    RiskAssessmentModel,
    VerifierAuditModel,
    VerifierDecisionModel,
)
from app.verifier.repository import (
    VerifierAuditRepository,
    VerifierComplianceRepository,
    VerifierDecisionRepository,
    VerifierPolicyViolationRepository,
    VerifierRiskRepository,
)
from app.verifier.schemas import VerifierDecisionRead, VerifierHistoryRead


class SqlAlchemyVerifierDecisionRepository(VerifierDecisionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, decision: VerifierDecisionRead) -> VerifierDecisionRead:
        row = VerifierDecisionModel(
            id=decision.id,
            tenant_id=decision.tenant_id,
            agent_id=decision.agent_id,
            conversation_id=decision.conversation_id,
            planner_decision_id=decision.planner_decision_id,
            approved=decision.approved,
            outcome=decision.outcome.value,
            risk_level=decision.risk_level.value,
            requires_confirmation=decision.requires_confirmation,
            requires_human=decision.requires_human,
            reason=decision.reason,
            corrected_tool_arguments=decision.corrected_tool_arguments,
            warnings=decision.warnings,
            violations=decision.violations,
            identity_status=decision.identity_status,
            latency_ms=decision.latency_ms,
            token_estimate=decision.token_estimate,
            model_provider=decision.provider_name,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return VerifierDecisionRead.model_validate(row)

    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 20,
    ) -> list[VerifierDecisionRead]:
        result = await self._session.execute(
            select(VerifierDecisionModel)
            .where(
                VerifierDecisionModel.tenant_id == tenant_id,
                VerifierDecisionModel.agent_id == agent_id,
                VerifierDecisionModel.conversation_id == conversation_id,
            )
            .order_by(VerifierDecisionModel.created_at.desc())
            .limit(limit)
        )
        return [VerifierDecisionRead.model_validate(r) for r in result.scalars().all()]

    async def metrics_snapshot(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
    ) -> dict:
        query = select(VerifierDecisionModel).where(
            VerifierDecisionModel.tenant_id == tenant_id,
            VerifierDecisionModel.agent_id == agent_id,
        )
        if conversation_id:
            query = query.where(VerifierDecisionModel.conversation_id == conversation_id)
        result = await self._session.execute(query)
        rows = list(result.scalars().all())
        if not rows:
            return {}
        risk_dist: dict[str, int] = {}
        for r in rows:
            risk_dist[r.risk_level] = risk_dist.get(r.risk_level, 0) + 1
        return {
            "total_verifications": len(rows),
            "approval_count": sum(1 for r in rows if r.approved),
            "rejection_count": sum(1 for r in rows if not r.approved),
            "escalation_count": sum(1 for r in rows if r.outcome == "escalated"),
            "confirmation_required_count": sum(1 for r in rows if r.requires_confirmation),
            "average_latency_ms": sum(r.latency_ms for r in rows) / len(rows),
            "risk_distribution": risk_dist,
        }


class SqlAlchemyVerifierAuditRepository(VerifierAuditRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, entry: VerifierHistoryRead) -> VerifierHistoryRead:
        row = VerifierAuditModel(
            id=entry.id,
            tenant_id=entry.tenant_id,
            agent_id=entry.agent_id,
            conversation_id=entry.conversation_id,
            decision_id=entry.decision_id,
            status=entry.status,
            planner_output=entry.planner_output,
            verifier_result=entry.verifier_result,
            validation_failures=entry.validation_failures,
            policy_violations=entry.policy_violations,
            risk_score=entry.risk_score,
            identity_status=entry.identity_status,
            tool_validation=None,
            occurred_at=entry.occurred_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return VerifierHistoryRead.model_validate(row)

    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ) -> list[VerifierHistoryRead]:
        result = await self._session.execute(
            select(VerifierAuditModel)
            .where(
                VerifierAuditModel.tenant_id == tenant_id,
                VerifierAuditModel.agent_id == agent_id,
                VerifierAuditModel.conversation_id == conversation_id,
            )
            .order_by(VerifierAuditModel.occurred_at.desc())
            .limit(limit)
        )
        return [VerifierHistoryRead.model_validate(r) for r in result.scalars().all()]


class SqlAlchemyVerifierRiskRepository(VerifierRiskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_assessment(self, assessment: dict) -> None:
        row = RiskAssessmentModel(**assessment)
        self._session.add(row)
        await self._session.flush()


class SqlAlchemyVerifierPolicyViolationRepository(VerifierPolicyViolationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_violations(self, decision_id: UUID, violations: list[dict]) -> None:
        for v in violations:
            row = PolicyViolationModel(decision_id=decision_id, **v)
            self._session.add(row)
        await self._session.flush()


class SqlAlchemyVerifierComplianceRepository(VerifierComplianceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_checks(self, decision_id: UUID, checks: list[dict]) -> None:
        for c in checks:
            row = ComplianceCheckModel(decision_id=decision_id, **c)
            self._session.add(row)
        await self._session.flush()
