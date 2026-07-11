"""MemoryManager port — single entry point for the Planner."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.enums import SessionState
from app.memory.schemas import (
    AppendMessageRequest,
    AppendToolResultRequest,
    CreateSessionRequest,
    MemoryMetricsSnapshot,
    PlannerContext,
    SessionRead,
    StructuredSummary,
    TurnRead,
    WorkingMemorySetRequest,
)


class MemoryManager(ABC):
    @abstractmethod
    async def create_session(self, request: CreateSessionRequest) -> SessionRead:
        raise NotImplementedError

    @abstractmethod
    async def append_message(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        data: AppendMessageRequest,
    ) -> TurnRead:
        raise NotImplementedError

    @abstractmethod
    async def append_tool_result(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        data: AppendToolResultRequest,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_state(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        state: SessionState,
    ) -> SessionRead:
        raise NotImplementedError

    @abstractmethod
    async def set_working_memory(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        data: WorkingMemorySetRequest,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_context(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        retrieved_knowledge: list[str] | None = None,
        agent_configuration: dict | None = None,
        tenant_policies: dict | None = None,
    ) -> PlannerContext:
        raise NotImplementedError

    @abstractmethod
    async def generate_summary(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> StructuredSummary:
        raise NotImplementedError

    @abstractmethod
    async def get_summary(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> StructuredSummary | None:
        raise NotImplementedError

    @abstractmethod
    async def clear_session(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def archive(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead:
        raise NotImplementedError

    @abstractmethod
    async def get_session(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead:
        raise NotImplementedError

    @abstractmethod
    async def get_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 100,
    ) -> list[TurnRead]:
        raise NotImplementedError

    @abstractmethod
    async def get_metrics(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> MemoryMetricsSnapshot:
        raise NotImplementedError
