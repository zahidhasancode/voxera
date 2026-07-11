"""Memory type interfaces — ports for each memory domain."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.memory.schemas import (
    AppendMessageRequest,
    AppendToolResultRequest,
    PlannerContext,
    StructuredSummary,
    SummaryRead,
    ToolExecutionRead,
    TurnRead,
    WorkingMemoryRead,
)


class ConversationMemory(ABC):
    @abstractmethod
    async def append_turn(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        data: AppendMessageRequest,
    ) -> TurnRead:
        raise NotImplementedError

    @abstractmethod
    async def get_turns(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 100,
    ) -> list[TurnRead]:
        raise NotImplementedError


class WorkingMemory(ABC):
    @abstractmethod
    async def set(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        key: str,
        value: str,
        *,
        language: str | None = None,
        is_sensitive: bool = False,
    ) -> WorkingMemoryRead:
        raise NotImplementedError

    @abstractmethod
    async def get_all(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    async def clear(self, tenant_id: UUID, agent_id: UUID, conversation_id: UUID) -> int:
        raise NotImplementedError


class SessionMemory(ABC):
    @abstractmethod
    async def get_state(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def update_state(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        state: str,
    ) -> None:
        raise NotImplementedError


class ToolMemory(ABC):
    @abstractmethod
    async def record(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        data: AppendToolResultRequest,
    ) -> ToolExecutionRead:
        raise NotImplementedError

    @abstractmethod
    async def get_recent(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 20,
    ) -> list[ToolExecutionRead]:
        raise NotImplementedError


class KnowledgeMemory(ABC):
    """Snapshot of retrieved knowledge attached to session — does not call RAG engine."""

    @abstractmethod
    async def attach(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        excerpts: list[str],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> list[str]:
        raise NotImplementedError


class SummaryMemory(ABC):
    @abstractmethod
    async def save(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        summary: StructuredSummary,
        *,
        turn_count: int,
    ) -> SummaryRead:
        raise NotImplementedError

    @abstractmethod
    async def get_latest(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SummaryRead | None:
        raise NotImplementedError


class LongTermMemory(ABC):
    """Future port for cross-session persistent memory."""

    @abstractmethod
    async def store(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        user_id: str,
        fact: str,
        *,
        metadata: dict | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def recall(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        user_id: str,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[str]:
        raise NotImplementedError
