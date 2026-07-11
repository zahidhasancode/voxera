"""Tool registry repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.tools.schemas.crud import ToolCreate, ToolRead, ToolUpdate


class ToolRepository(ABC):
    @abstractmethod
    async def create(self, data: ToolCreate) -> ToolRead:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, tool_id: UUID) -> ToolRead | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(self, tenant_id: UUID, slug: str) -> ToolRead | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[ToolRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        tenant_id: UUID,
        tool_id: UUID,
        data: ToolUpdate,
    ) -> ToolRead | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, tenant_id: UUID, tool_id: UUID) -> bool:
        raise NotImplementedError
