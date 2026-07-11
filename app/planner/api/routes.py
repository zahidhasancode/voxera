"""Planner REST API — thin delegation to PlannerService."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies import get_planner_service, map_domain_errors
from app.planner.schemas import (
    PlanRequest,
    PlannerDecisionRead,
    PlannerHistoryRead,
    PlannerMetricsSnapshot,
    PlannerPlan,
)
from app.planner.services.planner_service import PlannerService

router = APIRouter()


@router.post("/plan", response_model=PlannerPlan)
async def create_plan(
    tenant_id: UUID,
    agent_id: UUID,
    body: PlanRequest,
    service: PlannerService = Depends(get_planner_service),
) -> PlannerPlan:
    try:
        return await service.plan(tenant_id, agent_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/history", response_model=list[PlannerHistoryRead])
async def get_planner_history(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    service: PlannerService = Depends(get_planner_service),
) -> list[PlannerHistoryRead]:
    try:
        return await service.get_history(tenant_id, agent_id, conversation_id, limit=limit)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/decisions", response_model=list[PlannerDecisionRead])
async def get_planner_decisions(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID = Query(...),
    limit: int = Query(default=20, ge=1, le=100),
    service: PlannerService = Depends(get_planner_service),
) -> list[PlannerDecisionRead]:
    try:
        return await service.get_decisions(tenant_id, agent_id, conversation_id, limit=limit)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/metrics", response_model=PlannerMetricsSnapshot)
async def get_planner_metrics(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID | None = Query(default=None),
    service: PlannerService = Depends(get_planner_service),
) -> PlannerMetricsSnapshot:
    try:
        return await service.get_metrics(tenant_id, agent_id, conversation_id=conversation_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc
