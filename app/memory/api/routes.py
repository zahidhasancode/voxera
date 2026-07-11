"""Memory REST API — thin delegation to MemoryManager."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_memory_manager, map_domain_errors
from app.memory.manager.memory_manager import MemoryManager
from app.memory.schemas import (
    MemoryMetricsSnapshot,
    PlannerContext,
    SessionRead,
    StructuredSummary,
    TurnRead,
)

router = APIRouter()


@router.get("/session", response_model=SessionRead)
async def get_memory_session(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID = Query(...),
    manager: MemoryManager = Depends(get_memory_manager),
) -> SessionRead:
    try:
        return await manager.get_session(tenant_id, agent_id, conversation_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/history", response_model=list[TurnRead])
async def get_memory_history(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID = Query(...),
    limit: int = Query(default=100, ge=1, le=500),
    manager: MemoryManager = Depends(get_memory_manager),
) -> list[TurnRead]:
    try:
        return await manager.get_history(tenant_id, agent_id, conversation_id, limit=limit)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/summary", response_model=StructuredSummary)
async def get_memory_summary(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID = Query(...),
    refresh: bool = Query(default=False),
    manager: MemoryManager = Depends(get_memory_manager),
) -> StructuredSummary:
    try:
        if refresh:
            return await manager.generate_summary(tenant_id, agent_id, conversation_id)
        existing = await manager.get_summary(tenant_id, agent_id, conversation_id)
        if existing:
            return existing
        return await manager.generate_summary(tenant_id, agent_id, conversation_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/context", response_model=PlannerContext)
async def get_planner_context(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID = Query(...),
    manager: MemoryManager = Depends(get_memory_manager),
) -> PlannerContext:
    try:
        return await manager.get_context(tenant_id, agent_id, conversation_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory_session(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID = Query(...),
    manager: MemoryManager = Depends(get_memory_manager),
) -> None:
    try:
        await manager.clear_session(tenant_id, agent_id, conversation_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/metrics", response_model=MemoryMetricsSnapshot)
async def get_memory_metrics(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID = Query(...),
    manager: MemoryManager = Depends(get_memory_manager),
) -> MemoryMetricsSnapshot:
    return await manager.get_metrics(tenant_id, agent_id, conversation_id)
