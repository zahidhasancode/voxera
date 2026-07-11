"""Verifier service port."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.verifier.schemas import VerifyRequest, VerifierHistoryRead, VerifierMetricsSnapshot, VerifierResult


class VerifierService(ABC):
    @abstractmethod
    async def verify(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: VerifyRequest,
    ) -> VerifierResult:
        ...

    @abstractmethod
    async def get_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ) -> list[VerifierHistoryRead]:
        ...

    @abstractmethod
    async def get_metrics(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
    ) -> VerifierMetricsSnapshot:
        ...
