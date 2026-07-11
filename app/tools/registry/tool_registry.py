"""Tool registry port — Planner interacts ONLY with this interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.tools.schemas.execution import (
    ToolDefinitionRead,
    ToolExecuteRequest,
    ToolExecutionRead,
    ToolExecutionResult,
    ToolMetricsSnapshot,
    ToolTestRequest,
)


class ToolRegistry(ABC):
    @abstractmethod
    async def list_tools(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        enabled_only: bool = True,
    ) -> list[ToolDefinitionRead]:
        ...

    @abstractmethod
    async def get_tool(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        tool_slug: str,
    ) -> ToolDefinitionRead:
        ...

    @abstractmethod
    async def enable_tool(self, tenant_id: UUID, tool_slug: str) -> None:
        ...

    @abstractmethod
    async def disable_tool(self, tenant_id: UUID, tool_slug: str) -> None:
        ...

    @abstractmethod
    async def execute(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: ToolExecuteRequest,
    ) -> ToolExecutionResult:
        ...

    @abstractmethod
    async def test(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: ToolTestRequest,
    ) -> ToolExecutionResult:
        ...

    @abstractmethod
    async def get_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
        tool_slug: str | None = None,
        limit: int = 50,
    ) -> list[ToolExecutionRead]:
        ...

    @abstractmethod
    async def get_metrics(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        tool_slug: str | None = None,
    ) -> ToolMetricsSnapshot:
        ...
