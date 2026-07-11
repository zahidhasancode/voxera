"""Tool registry REST endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_tool_service, map_domain_errors
from app.core.schemas import PaginatedResponse
from app.tools.schemas import ToolCreate, ToolRead, ToolUpdate
from app.tools.service import ToolService

router = APIRouter()


class ToolListResponse(PaginatedResponse):
    items: list[ToolRead]


@router.post("", response_model=ToolRead, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tenant_id: UUID,
    body: ToolCreate,
    service: ToolService = Depends(get_tool_service),
) -> ToolRead:
    payload = body.model_copy(update={"tenant_id": tenant_id})
    return await service.create_tool(payload)


@router.get("", response_model=ToolListResponse)
async def list_tools(
    tenant_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: ToolService = Depends(get_tool_service),
) -> ToolListResponse:
    items, total = await service.list_tools(tenant_id, offset=offset, limit=limit)
    return ToolListResponse(total=total, offset=offset, limit=limit, items=items)


@router.get("/{tool_id}", response_model=ToolRead)
async def get_tool(
    tenant_id: UUID,
    tool_id: UUID,
    service: ToolService = Depends(get_tool_service),
) -> ToolRead:
    try:
        return await service.get_tool(tenant_id, tool_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.patch("/{tool_id}", response_model=ToolRead)
async def update_tool(
    tenant_id: UUID,
    tool_id: UUID,
    body: ToolUpdate,
    service: ToolService = Depends(get_tool_service),
) -> ToolRead:
    try:
        return await service.update_tool(tenant_id, tool_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tenant_id: UUID,
    tool_id: UUID,
    service: ToolService = Depends(get_tool_service),
) -> None:
    try:
        await service.delete_tool(tenant_id, tool_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc
