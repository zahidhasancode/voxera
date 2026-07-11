"""Tool execution REST API — thin delegation to ToolRegistry."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies import get_tool_registry, map_domain_errors
from app.tools.registry.tool_registry import ToolRegistry
from app.tools.schemas.execution import (
    ToolDefinitionRead,
    ToolExecuteRequest,
    ToolExecutionRead,
    ToolExecutionResult,
    ToolMetricsSnapshot,
    ToolTestRequest,
)

router = APIRouter()


@router.get("", response_model=list[ToolDefinitionRead])
async def list_tools(
    tenant_id: UUID,
    agent_id: UUID,
    enabled_only: bool = Query(default=True),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> list[ToolDefinitionRead]:
    try:
        return await registry.list_tools(tenant_id, agent_id, enabled_only=enabled_only)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/history", response_model=list[ToolExecutionRead])
async def get_tool_history(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID | None = Query(default=None),
    tool_slug: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> list[ToolExecutionRead]:
    try:
        return await registry.get_history(
            tenant_id,
            agent_id,
            conversation_id=conversation_id,
            tool_slug=tool_slug,
            limit=limit,
        )
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/metrics", response_model=ToolMetricsSnapshot)
async def get_tool_metrics(
    tenant_id: UUID,
    agent_id: UUID,
    tool_slug: str | None = Query(default=None),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ToolMetricsSnapshot:
    try:
        return await registry.get_metrics(tenant_id, agent_id, tool_slug=tool_slug)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.post("/test", response_model=ToolExecutionResult)
async def test_tool(
    tenant_id: UUID,
    agent_id: UUID,
    body: ToolTestRequest,
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ToolExecutionResult:
    try:
        return await registry.test(tenant_id, agent_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.post("/execute", response_model=ToolExecutionResult)
async def execute_tool(
    tenant_id: UUID,
    agent_id: UUID,
    body: ToolExecuteRequest,
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ToolExecutionResult:
    try:
        return await registry.execute(tenant_id, agent_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/{tool_slug}", response_model=ToolDefinitionRead)
async def get_tool(
    tenant_id: UUID,
    agent_id: UUID,
    tool_slug: str,
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ToolDefinitionRead:
    try:
        return await registry.get_tool(tenant_id, agent_id, tool_slug)
    except Exception as exc:
        raise map_domain_errors(exc) from exc
