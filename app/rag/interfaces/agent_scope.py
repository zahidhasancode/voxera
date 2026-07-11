"""Agent knowledge scope resolver port."""

from abc import ABC, abstractmethod
from uuid import UUID


class AgentKnowledgeScope(ABC):
    """Determines which knowledge sources an agent may retrieve from."""

    @abstractmethod
    async def resolve_source_ids(
        self,
        tenant_id: UUID,
        agent_id: UUID,
    ) -> list[UUID] | None:
        """
        Return allowed source IDs, or None to allow all READY tenant sources.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_agent_language(self, tenant_id: UUID, agent_id: UUID) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def get_agent_system_prompt(self, tenant_id: UUID, agent_id: UUID) -> str | None:
        raise NotImplementedError
