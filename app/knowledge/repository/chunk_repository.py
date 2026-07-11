"""Knowledge chunk repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.knowledge.schemas.chunk import KnowledgeChunkCreate, KnowledgeChunkRead


class KnowledgeChunkRepository(ABC):
    @abstractmethod
    async def create_batch(self, chunks: list[KnowledgeChunkCreate]) -> list[KnowledgeChunkRead]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_source(
        self,
        tenant_id: UUID,
        source_id: UUID,
        *,
        offset: int = 0,
        limit: int = 500,
    ) -> tuple[list[KnowledgeChunkRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_source(self, tenant_id: UUID, source_id: UUID) -> int:
        raise NotImplementedError

    @abstractmethod
    async def update_vector_ids(
        self,
        tenant_id: UUID,
        chunk_vector_map: dict[str, str],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_ids(
        self,
        tenant_id: UUID,
        chunk_ids: list[UUID],
    ) -> list[KnowledgeChunkRead]:
        raise NotImplementedError
