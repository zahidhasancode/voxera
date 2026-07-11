"""Agent REST endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.agents.schemas import AgentCreate, AgentRead, AgentUpdate
from app.agents.service import AgentService
from app.api.v1.dependencies import get_agent_service, map_domain_errors
from app.core.schemas import PaginatedResponse

router = APIRouter()


class AgentListResponse(PaginatedResponse):
    items: list[AgentRead]


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    tenant_id: UUID,
    body: AgentCreate,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    payload = body.model_copy(update={"tenant_id": tenant_id})
    return await service.create_agent(payload)


@router.get("", response_model=AgentListResponse)
async def list_agents(
    tenant_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: AgentService = Depends(get_agent_service),
) -> AgentListResponse:
    items, total = await service.list_agents(tenant_id, offset=offset, limit=limit)
    return AgentListResponse(total=total, offset=offset, limit=limit, items=items)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    tenant_id: UUID,
    agent_id: UUID,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    try:
        return await service.get_agent(tenant_id, agent_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    tenant_id: UUID,
    agent_id: UUID,
    body: AgentUpdate,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    try:
        return await service.update_agent(tenant_id, agent_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    tenant_id: UUID,
    agent_id: UUID,
    service: AgentService = Depends(get_agent_service),
) -> None:
    try:
        await service.delete_agent(tenant_id, agent_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc
