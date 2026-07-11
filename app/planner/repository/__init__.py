"""Planner repository ports."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.planner.schemas import (
    PlannerDecisionRead,
    PlannerHistoryRead,
    PlannerSessionRead,
)


class PlannerSessionRepository(ABC):
    @abstractmethod
    async def get_or_create(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        language: str = "en",
    ) -> PlannerSessionRead:
        ...

    @abstractmethod
    async def increment_steps(self, session_id: UUID, *, intent: str | None = None) -> PlannerSessionRead:
        ...


class PlannerDecisionRepository(ABC):
    @abstractmethod
    async def create(self, decision: PlannerDecisionRead) -> PlannerDecisionRead:
        ...

    @abstractmethod
    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 20,
    ) -> list[PlannerDecisionRead]:
        ...


class PlannerHistoryRepository(ABC):
    @abstractmethod
    async def append(self, entry: PlannerHistoryRead) -> PlannerHistoryRead:
        ...

    @abstractmethod
    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ) -> list[PlannerHistoryRead]:
        ...


class PlannerMetricsRepository(ABC):
    @abstractmethod
    async def snapshot(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
    ) -> dict:
        ...
