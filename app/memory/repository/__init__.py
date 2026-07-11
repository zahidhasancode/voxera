"""Memory repository ports."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.core.enums import ConversationStatus, SessionState
from app.memory.schemas import (
    AppendMessageRequest,
    AppendToolResultRequest,
    CreateSessionRequest,
    SessionRead,
    StructuredSummary,
    SummaryRead,
    ToolExecutionRead,
    TurnRead,
    WorkingMemoryRead,
)


class ConversationRepository(ABC):
    @abstractmethod
    async def create(self, data: CreateSessionRequest, *, expires_at: datetime | None) -> SessionRead:
        raise NotImplementedError

    @abstractmethod
    async def get(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead | None:
        raise NotImplementedError

    @abstractmethod
    async def update_state(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        state: SessionState,
    ) -> SessionRead | None:
        raise NotImplementedError

    @abstractmethod
    async def update_language(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        language: str,
    ) -> SessionRead | None:
        raise NotImplementedError

    @abstractmethod
    async def increment_turn_count(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_completed(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_archived(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_expired(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead | None:
        raise NotImplementedError


class ConversationTurnRepository(ABC):
    @abstractmethod
    async def append(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        turn_index: int,
        data: AppendMessageRequest,
    ) -> TurnRead:
        raise NotImplementedError

    @abstractmethod
    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TurnRead]:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> int:
        raise NotImplementedError


class WorkingMemoryRepository(ABC):
    @abstractmethod
    async def upsert(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        key: str,
        value: str,
        *,
        value_type: str = "string",
        language: str | None = None,
        is_sensitive: bool = False,
        expires_at: datetime | None = None,
    ) -> WorkingMemoryRead:
        raise NotImplementedError

    @abstractmethod
    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> list[WorkingMemoryRead]:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> int:
        raise NotImplementedError


class ToolExecutionRepository(ABC):
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
    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 20,
    ) -> list[ToolExecutionRead]:
        raise NotImplementedError


class ConversationSummaryRepository(ABC):
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
