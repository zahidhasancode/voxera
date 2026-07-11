"""Planner subsystem factory."""

from functools import lru_cache

from app.infrastructure.planner.planner_service import PlannerServiceImpl
from app.infrastructure.repositories.planner.repositories import (
    SqlAlchemyPlannerDecisionRepository,
    SqlAlchemyPlannerHistoryRepository,
    SqlAlchemyPlannerMetricsRepository,
    SqlAlchemyPlannerSessionRepository,
)
from app.infrastructure.memory.factory import build_memory_manager
from app.infrastructure.tools.factory import build_tool_registry
from app.planner.cache.base import InMemoryPlannerCache, PlannerCache
from app.planner.metrics.collector import PlannerMetricsCollector
from app.planner.models.structured_model import StructuredPlannerModel
from app.planner.services.planner_service import PlannerService


@lru_cache
def get_planner_cache() -> PlannerCache:
    return InMemoryPlannerCache()


@lru_cache
def get_planner_metrics_collector() -> PlannerMetricsCollector:
    return PlannerMetricsCollector()


def build_planner_service(session) -> PlannerService:
    return PlannerServiceImpl(
        memory_manager=build_memory_manager(session),
        tool_registry=build_tool_registry(session),
        sessions=SqlAlchemyPlannerSessionRepository(session),
        decisions=SqlAlchemyPlannerDecisionRepository(session),
        history=SqlAlchemyPlannerHistoryRepository(session),
        metrics_repo=SqlAlchemyPlannerMetricsRepository(session),
        model=StructuredPlannerModel(),
        cache=get_planner_cache(),
        metrics=get_planner_metrics_collector(),
    )
