"""Agent configuration REST endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies import get_agent_configuration_service, map_domain_errors
from app.configuration.schemas import (
    AgentConfigurationCreate,
    AgentConfigurationRead,
    AgentConfigurationUpdate,
)
from app.configuration.service import AgentConfigurationService

router = APIRouter()


@router.post("", response_model=AgentConfigurationRead, status_code=status.HTTP_201_CREATED)
async def create_agent_configuration(
    tenant_id: UUID,
    agent_id: UUID,
    body: AgentConfigurationCreate,
    service: AgentConfigurationService = Depends(get_agent_configuration_service),
) -> AgentConfigurationRead:
    payload = body.model_copy(update={"tenant_id": tenant_id, "agent_id": agent_id})
    return await service.create_configuration(payload)


@router.get("", response_model=AgentConfigurationRead)
async def get_agent_configuration(
    tenant_id: UUID,
    agent_id: UUID,
    service: AgentConfigurationService = Depends(get_agent_configuration_service),
) -> AgentConfigurationRead:
    try:
        return await service.get_configuration(tenant_id, agent_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.patch("", response_model=AgentConfigurationRead)
async def update_agent_configuration(
    tenant_id: UUID,
    agent_id: UUID,
    body: AgentConfigurationUpdate,
    service: AgentConfigurationService = Depends(get_agent_configuration_service),
) -> AgentConfigurationRead:
    try:
        return await service.update_configuration(tenant_id, agent_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_configuration(
    tenant_id: UUID,
    agent_id: UUID,
    service: AgentConfigurationService = Depends(get_agent_configuration_service),
) -> None:
    try:
        await service.delete_configuration(tenant_id, agent_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc
