"""Tool registry application service interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.tools.schemas import ToolCreate, ToolRead, ToolUpdate


class ToolService(ABC):
    @abstractmethod
    async def create_tool(self, data: ToolCreate) -> ToolRead:
        raise NotImplementedError

    @abstractmethod
    async def get_tool(self, tenant_id: UUID, tool_id: UUID) -> ToolRead:
        raise NotImplementedError

    @abstractmethod
    async def list_tools(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[ToolRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def update_tool(
        self,
        tenant_id: UUID,
        tool_id: UUID,
        data: ToolUpdate,
    ) -> ToolRead:
        raise NotImplementedError

    @abstractmethod
    async def delete_tool(self, tenant_id: UUID, tool_id: UUID) -> None:
        raise NotImplementedError
