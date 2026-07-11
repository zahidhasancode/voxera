"""Knowledge source repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.core.enums import (
    KnowledgeEmbeddingStatus,
    KnowledgeProcessingStage,
    KnowledgeSourceStatus,
)
from app.knowledge.schemas.source import (
    KnowledgeSourceCreate,
    KnowledgeSourceRead,
    KnowledgeSourceStatusSummary,
    KnowledgeSourceUpdate,
)


class KnowledgeSourceRepository(ABC):
    @abstractmethod
    async def create(self, data: KnowledgeSourceCreate) -> KnowledgeSourceRead:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, source_id: UUID) -> KnowledgeSourceRead | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
        status: KnowledgeSourceStatus | None = None,
    ) -> tuple[list[KnowledgeSourceRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        tenant_id: UUID,
        source_id: UUID,
        data: KnowledgeSourceUpdate,
    ) -> KnowledgeSourceRead | None:
        raise NotImplementedError

    @abstractmethod
    async def update_file_info(
        self,
        tenant_id: UUID,
        source_id: UUID,
        *,
        file_path: str,
        file_size_bytes: int,
        content_type: str | None,
        original_filename: str | None,
    ) -> KnowledgeSourceRead | None:
        raise NotImplementedError

    @abstractmethod
    async def update_processing_state(
        self,
        tenant_id: UUID,
        source_id: UUID,
        *,
        status: KnowledgeSourceStatus | None = None,
        stage: KnowledgeProcessingStage | None = None,
        progress_pct: int | None = None,
        processing_started_at: datetime | None = None,
        processing_completed_at: datetime | None = None,
        processing_error: str | None = None,
        chunk_count: int | None = None,
        embedding_count: int | None = None,
        embedding_status: KnowledgeEmbeddingStatus | None = None,
    ) -> KnowledgeSourceRead | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, tenant_id: UUID, source_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_status_summary(self, tenant_id: UUID) -> KnowledgeSourceStatusSummary:
        raise NotImplementedError

    @abstractmethod
    async def list_by_ids(
        self,
        tenant_id: UUID,
        source_ids: list[UUID],
    ) -> list[KnowledgeSourceRead]:
        raise NotImplementedError
