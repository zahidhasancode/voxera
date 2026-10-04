"""Knowledge source application service interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.knowledge.schemas.source import (
    KnowledgeReprocessRequest,
    KnowledgeSourceCreate,
    KnowledgeSourceFrontendRead,
    KnowledgeSourceStatusSummary,
    KnowledgeSourceUpdate,
)


class KnowledgeSourceService(ABC):
    @abstractmethod
    async def upload_file(
        self,
        tenant_id: UUID,
        *,
        title: str,
        source_type: str,
        file_content: bytes,
        filename: str,
        content_type: str | None,
        chunk_config: dict | None = None,
    ) -> KnowledgeSourceFrontendRead:
        raise NotImplementedError

    @abstractmethod
    async def create_from_url(
        self,
        tenant_id: UUID,
        data: KnowledgeSourceCreate,
    ) -> KnowledgeSourceFrontendRead:
        raise NotImplementedError

    @abstractmethod
    async def get_source(self, tenant_id: UUID, source_id: UUID) -> KnowledgeSourceFrontendRead:
        raise NotImplementedError

    @abstractmethod
    async def list_sources(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[KnowledgeSourceFrontendRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def delete_source(self, tenant_id: UUID, source_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def reprocess(
        self,
        tenant_id: UUID,
        request: KnowledgeReprocessRequest,
    ) -> list[KnowledgeSourceFrontendRead]:
        raise NotImplementedError

    @abstractmethod
    async def get_status_summary(self, tenant_id: UUID) -> KnowledgeSourceStatusSummary:
        raise NotImplementedError

    @abstractmethod
    async def update_source(
        self,
        tenant_id: UUID,
        source_id: UUID,
        data: KnowledgeSourceUpdate,
    ) -> KnowledgeSourceFrontendRead:
        raise NotImplementedError
