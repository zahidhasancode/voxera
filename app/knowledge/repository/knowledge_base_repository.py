"""Knowledge base repository interface (Sprint 1)."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.knowledge.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate


class KnowledgeBaseRepository(ABC):
    @abstractmethod
    async def create(self, data: KnowledgeBaseCreate) -> KnowledgeBaseRead:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
    ) -> KnowledgeBaseRead | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[KnowledgeBaseRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        data: KnowledgeBaseUpdate,
    ) -> KnowledgeBaseRead | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, tenant_id: UUID, knowledge_base_id: UUID) -> bool:
        raise NotImplementedError
