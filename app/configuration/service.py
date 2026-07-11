"""Configuration application service interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.configuration.schemas import (
    AgentConfigurationCreate,
    AgentConfigurationRead,
    AgentConfigurationUpdate,
)


class AgentConfigurationService(ABC):
    @abstractmethod
    async def create_configuration(
        self,
        data: AgentConfigurationCreate,
    ) -> AgentConfigurationRead:
        raise NotImplementedError

    @abstractmethod
    async def get_configuration(
        self,
        tenant_id: UUID,
        agent_id: UUID,
    ) -> AgentConfigurationRead:
        raise NotImplementedError

    @abstractmethod
    async def update_configuration(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        data: AgentConfigurationUpdate,
    ) -> AgentConfigurationRead:
        raise NotImplementedError

    @abstractmethod
    async def delete_configuration(self, tenant_id: UUID, agent_id: UUID) -> None:
        raise NotImplementedError
