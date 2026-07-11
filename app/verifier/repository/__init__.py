"""Verifier repository ports."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.verifier.schemas import VerifierDecisionRead, VerifierHistoryRead


class VerifierDecisionRepository(ABC):
    @abstractmethod
    async def create(self, decision: VerifierDecisionRead) -> VerifierDecisionRead:
        ...

    @abstractmethod
    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 20,
    ) -> list[VerifierDecisionRead]:
        ...

    @abstractmethod
    async def metrics_snapshot(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
    ) -> dict:
        ...


class VerifierAuditRepository(ABC):
    @abstractmethod
    async def append(self, entry: VerifierHistoryRead) -> VerifierHistoryRead:
        ...

    @abstractmethod
    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ) -> list[VerifierHistoryRead]:
        ...


class VerifierComplianceRepository(ABC):
    @abstractmethod
    async def record_checks(self, decision_id: UUID, checks: list[dict]) -> None:
        ...


class VerifierPolicyViolationRepository(ABC):
    @abstractmethod
    async def record_violations(self, decision_id: UUID, violations: list[dict]) -> None:
        ...


class VerifierRiskRepository(ABC):
    @abstractmethod
    async def record_assessment(self, assessment: dict) -> None:
        ...
