"""Agent application service interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.agents.schemas import AgentCreate, AgentRead, AgentUpdate


class AgentService(ABC):
    @abstractmethod
    async def create_agent(self, data: AgentCreate) -> AgentRead:
        raise NotImplementedError

    @abstractmethod
    async def get_agent(self, tenant_id: UUID, agent_id: UUID) -> AgentRead:
        raise NotImplementedError

    @abstractmethod
    async def list_agents(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AgentRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def update_agent(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        data: AgentUpdate,
    ) -> AgentRead:
        raise NotImplementedError

    @abstractmethod
    async def delete_agent(self, tenant_id: UUID, agent_id: UUID) -> None:
        raise NotImplementedError
