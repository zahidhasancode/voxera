"""Agent knowledge scope implementation."""

from uuid import UUID

from app.agents.repository import AgentRepository
from app.core.enums import AgentStatus
from app.core.exceptions import NotFoundError, UnauthorizedAgentAccessError
from app.rag.interfaces.agent_scope import AgentKnowledgeScope


class SqlAlchemyAgentKnowledgeScope(AgentKnowledgeScope):
    def __init__(self, agent_repository: AgentRepository) -> None:
        self._agents = agent_repository

    async def resolve_source_ids(
        self,
        tenant_id: UUID,
        agent_id: UUID,
    ) -> list[UUID] | None:
        await self._require_active_agent(tenant_id, agent_id)
        return None  # All READY tenant sources; extend via agent configuration in Sprint 3

    async def get_agent_language(self, tenant_id: UUID, agent_id: UUID) -> str | None:
        agent = await self._agents.get_by_id(tenant_id, agent_id)
        return agent.language if agent else None

    async def get_agent_system_prompt(self, tenant_id: UUID, agent_id: UUID) -> str | None:
        agent = await self._agents.get_by_id(tenant_id, agent_id)
        return agent.system_prompt if agent else None

    async def _require_active_agent(self, tenant_id: UUID, agent_id: UUID):
        agent = await self._agents.get_by_id(tenant_id, agent_id)
        if agent is None:
            raise NotFoundError(f"Agent {agent_id} not found")
        if agent.status != AgentStatus.ACTIVE:
            raise UnauthorizedAgentAccessError(
                f"Agent {agent_id} is not active (status={agent.status})"
            )
        return agent
