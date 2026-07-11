"""Planner model provider interface."""

from abc import ABC, abstractmethod

from app.planner.schemas import OptimizedPlannerContext, PlannerInput, PlannerPlan


class PlannerModel(ABC):
    """Provider-independent planning model."""

    @abstractmethod
    async def plan(self, context: OptimizedPlannerContext, planner_input: PlannerInput) -> PlannerPlan:
        """Generate structured plan from optimized context."""

    @abstractmethod
    async def health(self) -> dict:
        """Provider health check."""

    @abstractmethod
    def estimate_tokens(self, context: OptimizedPlannerContext) -> int:
        """Estimate token usage for context."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...
