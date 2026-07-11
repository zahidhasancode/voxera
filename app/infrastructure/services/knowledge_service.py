"""Knowledge base service implementation."""

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.repositories.knowledge_repository import SqlAlchemyKnowledgeBaseRepository
from app.knowledge.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate
from app.knowledge.services.knowledge_base_service import KnowledgeBaseService


class KnowledgeBaseServiceImpl(KnowledgeBaseService):
    def __init__(self, repository: SqlAlchemyKnowledgeBaseRepository) -> None:
        self._repository = repository

    async def create_knowledge_base(self, data: KnowledgeBaseCreate) -> KnowledgeBaseRead:
        return await self._repository.create(data)

    async def get_knowledge_base(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
    ) -> KnowledgeBaseRead:
        row = await self._repository.get_by_id(tenant_id, knowledge_base_id)
        if row is None:
            raise NotFoundError(f"Knowledge base {knowledge_base_id} not found")
        return row

    async def list_knowledge_bases(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[KnowledgeBaseRead], int]:
        return await self._repository.list_by_tenant(tenant_id, offset=offset, limit=limit)

    async def update_knowledge_base(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        data: KnowledgeBaseUpdate,
    ) -> KnowledgeBaseRead:
        row = await self._repository.update(tenant_id, knowledge_base_id, data)
        if row is None:
            raise NotFoundError(f"Knowledge base {knowledge_base_id} not found")
        return row

    async def delete_knowledge_base(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
    ) -> None:
        deleted = await self._repository.delete(tenant_id, knowledge_base_id)
        if not deleted:
            raise NotFoundError(f"Knowledge base {knowledge_base_id} not found")
