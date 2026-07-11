"""Configuration repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.configuration.schemas import (
    AgentConfigurationCreate,
    AgentConfigurationRead,
    AgentConfigurationUpdate,
)


class AgentConfigurationRepository(ABC):
    @abstractmethod
    async def create(self, data: AgentConfigurationCreate) -> AgentConfigurationRead:
        raise NotImplementedError

    @abstractmethod
    async def get_by_agent_id(
        self,
        tenant_id: UUID,
        agent_id: UUID,
    ) -> AgentConfigurationRead | None:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        data: AgentConfigurationUpdate,
    ) -> AgentConfigurationRead | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, tenant_id: UUID, agent_id: UUID) -> bool:
        raise NotImplementedError
