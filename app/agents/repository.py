"""Agent repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.agents.schemas import AgentCreate, AgentRead, AgentUpdate


class AgentRepository(ABC):
    @abstractmethod
    async def create(self, data: AgentCreate) -> AgentRead:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, agent_id: UUID) -> AgentRead | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AgentRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        data: AgentUpdate,
    ) -> AgentRead | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, tenant_id: UUID, agent_id: UUID) -> bool:
        raise NotImplementedError
