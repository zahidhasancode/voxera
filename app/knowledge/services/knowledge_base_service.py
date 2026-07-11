"""Knowledge base application service interface (Sprint 1)."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.knowledge.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate


class KnowledgeBaseService(ABC):
    @abstractmethod
    async def create_knowledge_base(self, data: KnowledgeBaseCreate) -> KnowledgeBaseRead:
        raise NotImplementedError

    @abstractmethod
    async def get_knowledge_base(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
    ) -> KnowledgeBaseRead:
        raise NotImplementedError

    @abstractmethod
    async def list_knowledge_bases(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[KnowledgeBaseRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def update_knowledge_base(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        data: KnowledgeBaseUpdate,
    ) -> KnowledgeBaseRead:
        raise NotImplementedError

    @abstractmethod
    async def delete_knowledge_base(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
    ) -> None:
        raise NotImplementedError
