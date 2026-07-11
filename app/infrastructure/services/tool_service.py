"""Tool registry service implementation."""

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.repositories.tool_repository import SqlAlchemyToolRepository
from app.tools.schemas import ToolCreate, ToolRead, ToolUpdate
from app.tools.service import ToolService


class ToolServiceImpl(ToolService):
    def __init__(self, repository: SqlAlchemyToolRepository) -> None:
        self._repository = repository

    async def create_tool(self, data: ToolCreate) -> ToolRead:
        return await self._repository.create(data)

    async def get_tool(self, tenant_id: UUID, tool_id: UUID) -> ToolRead:
        row = await self._repository.get_by_id(tenant_id, tool_id)
        if row is None:
            raise NotFoundError(f"Tool {tool_id} not found")
        return row

    async def list_tools(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[ToolRead], int]:
        return await self._repository.list_by_tenant(tenant_id, offset=offset, limit=limit)

    async def update_tool(
        self,
        tenant_id: UUID,
        tool_id: UUID,
        data: ToolUpdate,
    ) -> ToolRead:
        row = await self._repository.update(tenant_id, tool_id, data)
        if row is None:
            raise NotFoundError(f"Tool {tool_id} not found")
        return row

    async def delete_tool(self, tenant_id: UUID, tool_id: UUID) -> None:
        deleted = await self._repository.delete(tenant_id, tool_id)
        if not deleted:
            raise NotFoundError(f"Tool {tool_id} not found")
