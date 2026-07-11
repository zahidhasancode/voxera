"""Prompt template provider — no hardcoded prompts in business logic."""

from abc import ABC, abstractmethod

from app.planner.schemas import OptimizedPlannerContext, PlannerInput


class PromptProvider(ABC):
    @abstractmethod
    def system_prompt(self, *, industry: str | None, language: str) -> str:
        ...

    @abstractmethod
    def planning_prompt(self, context: OptimizedPlannerContext, planner_input: PlannerInput) -> str:
        ...

    @abstractmethod
    def safety_prompt(self, *, tenant_policies: dict) -> str:
        ...

    @abstractmethod
    def industry_prompt(self, industry: str | None) -> str:
        ...

    @abstractmethod
    def tenant_prompt(self, tenant_policies: dict) -> str:
        ...

    @abstractmethod
    def language_prompt(self, language: str) -> str:
        ...
