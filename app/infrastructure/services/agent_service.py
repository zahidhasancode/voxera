"""Agent service implementation."""

from uuid import UUID

from app.agents.schemas import AgentCreate, AgentRead, AgentUpdate
from app.agents.service import AgentService
from app.core.exceptions import NotFoundError
from app.infrastructure.repositories.agent_repository import SqlAlchemyAgentRepository


class AgentServiceImpl(AgentService):
    def __init__(self, repository: SqlAlchemyAgentRepository) -> None:
        self._repository = repository

    async def create_agent(self, data: AgentCreate) -> AgentRead:
        return await self._repository.create(data)

    async def get_agent(self, tenant_id: UUID, agent_id: UUID) -> AgentRead:
        row = await self._repository.get_by_id(tenant_id, agent_id)
        if row is None:
            raise NotFoundError(f"Agent {agent_id} not found")
        return row

    async def list_agents(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AgentRead], int]:
        return await self._repository.list_by_tenant(tenant_id, offset=offset, limit=limit)

    async def update_agent(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        data: AgentUpdate,
    ) -> AgentRead:
        row = await self._repository.update(tenant_id, agent_id, data)
        if row is None:
            raise NotFoundError(f"Agent {agent_id} not found")
        return row

    async def delete_agent(self, tenant_id: UUID, agent_id: UUID) -> None:
        deleted = await self._repository.delete(tenant_id, agent_id)
        if not deleted:
            raise NotFoundError(f"Agent {agent_id} not found")
