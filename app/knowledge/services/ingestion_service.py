"""Knowledge ingestion service interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.knowledge.schemas.ingestion import IngestionJobStatus


class KnowledgeIngestionService(ABC):
    @abstractmethod
    async def enqueue_processing(self, tenant_id: UUID, source_id: UUID) -> IngestionJobStatus:
        raise NotImplementedError

    @abstractmethod
    async def run_processing(self, tenant_id: UUID, source_id: UUID) -> None:
        """Execute pipeline synchronously (used by background worker)."""
        raise NotImplementedError
