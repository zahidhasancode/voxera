"""Planner service port."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.planner.schemas import (
    PlanRequest,
    PlannerDecisionRead,
    PlannerHistoryRead,
    PlannerMetricsSnapshot,
    PlannerPlan,
)


class PlannerService(ABC):
    @abstractmethod
    async def plan(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: PlanRequest,
    ) -> PlannerPlan:
        ...

    @abstractmethod
    async def get_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ) -> list[PlannerHistoryRead]:
        ...

    @abstractmethod
    async def get_decisions(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 20,
    ) -> list[PlannerDecisionRead]:
        ...

    @abstractmethod
    async def get_metrics(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
    ) -> PlannerMetricsSnapshot:
        ...
