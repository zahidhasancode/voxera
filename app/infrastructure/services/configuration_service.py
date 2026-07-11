"""Agent configuration service implementation."""

from uuid import UUID

from app.configuration.schemas import (
    AgentConfigurationCreate,
    AgentConfigurationRead,
    AgentConfigurationUpdate,
)
from app.configuration.service import AgentConfigurationService
from app.core.exceptions import NotFoundError
from app.infrastructure.repositories.configuration_repository import (
    SqlAlchemyAgentConfigurationRepository,
)


class AgentConfigurationServiceImpl(AgentConfigurationService):
    def __init__(self, repository: SqlAlchemyAgentConfigurationRepository) -> None:
        self._repository = repository

    async def create_configuration(
        self,
        data: AgentConfigurationCreate,
    ) -> AgentConfigurationRead:
        return await self._repository.create(data)

    async def get_configuration(
        self,
        tenant_id: UUID,
        agent_id: UUID,
    ) -> AgentConfigurationRead:
        row = await self._repository.get_by_agent_id(tenant_id, agent_id)
        if row is None:
            raise NotFoundError(f"Configuration for agent {agent_id} not found")
        return row

    async def update_configuration(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        data: AgentConfigurationUpdate,
    ) -> AgentConfigurationRead:
        row = await self._repository.update(tenant_id, agent_id, data)
        if row is None:
            raise NotFoundError(f"Configuration for agent {agent_id} not found")
        return row

    async def delete_configuration(self, tenant_id: UUID, agent_id: UUID) -> None:
        deleted = await self._repository.delete(tenant_id, agent_id)
        if not deleted:
            raise NotFoundError(f"Configuration for agent {agent_id} not found")
