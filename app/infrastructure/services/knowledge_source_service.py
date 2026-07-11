"""Knowledge source service implementation."""

from uuid import UUID

from app.core.config import settings
from app.core.enums import KnowledgeSourceStatus, KnowledgeSourceType, VectorStoreType
from app.core.exceptions import NotFoundError
from app.infrastructure.knowledge.storage import KnowledgeFileStorage
from app.infrastructure.repositories.knowledge_source_repository import SqlAlchemyKnowledgeSourceRepository
from app.knowledge.chunking.models import ChunkConfig
from app.knowledge.ingestion.background import BackgroundIngestionProcessor
from app.knowledge.retrieval.vector_store import VectorStore
from app.knowledge.schemas.ingestion import IngestionJobSubmit
from app.knowledge.schemas.source import (
    KnowledgeReprocessRequest,
    KnowledgeSourceCreate,
    KnowledgeSourceFrontendRead,
    KnowledgeSourceRead,
    KnowledgeSourceStatusSummary,
    KnowledgeSourceUpdate,
)
from app.knowledge.services.source_service import KnowledgeSourceService
from app.knowledge.validation.document_validator import DocumentValidationError, DocumentValidator


class KnowledgeSourceServiceImpl(KnowledgeSourceService):
    def __init__(
        self,
        repository: SqlAlchemyKnowledgeSourceRepository,
        file_storage: KnowledgeFileStorage,
        background_processor: BackgroundIngestionProcessor,
        vector_store: VectorStore | None = None,
    ) -> None:
        self._repository = repository
        self._storage = file_storage
        self._background = background_processor
        self._vector_store = vector_store
        self._validator = DocumentValidator()

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
        parsed_type = KnowledgeSourceType(source_type)
        validation = self._validator.validate_upload(
            filename=filename,
            content=file_content,
            declared_type=parsed_type,
            content_type=content_type,
        )
        duplicate = await self._repository.find_by_file_hash(tenant_id, validation.file_hash)
        if duplicate is not None:
            raise DocumentValidationError(
                f"Duplicate document already uploaded as source {duplicate.id}"
            )
        config = (
            ChunkConfig(**chunk_config)
            if chunk_config
            else ChunkConfig(
                chunk_size=settings.KNOWLEDGE_DEFAULT_CHUNK_SIZE,
                chunk_overlap=settings.KNOWLEDGE_DEFAULT_CHUNK_OVERLAP,
            )
        )
        vector_store_type = (
            VectorStoreType(settings.KNOWLEDGE_DEFAULT_VECTOR_STORE)
            if settings.KNOWLEDGE_DEFAULT_VECTOR_STORE
            else None
        )

        create_data = KnowledgeSourceCreate(
            tenant_id=tenant_id,
            title=title,
            source_type=parsed_type,
            chunk_config=config,
            embedding_model=settings.KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER,
            vector_store_type=vector_store_type,
        )
        source = await self._repository.create(create_data)

        file_path = await self._storage.save(tenant_id, source.id, filename, file_content)
        source = await self._repository.update_file_info(
            tenant_id,
            source.id,
            file_path=file_path,
            file_size_bytes=len(file_content),
            content_type=content_type,
            original_filename=filename,
            file_hash=validation.file_hash,
        )
        assert source is not None

        await self._background.submit(
            IngestionJobSubmit(tenant_id=tenant_id, source_id=source.id)
        )
        return KnowledgeSourceFrontendRead.from_source(source)

    async def create_from_url(
        self,
        tenant_id: UUID,
        data: KnowledgeSourceCreate,
    ) -> KnowledgeSourceFrontendRead:
        payload = data.model_copy(update={"tenant_id": tenant_id})
        source = await self._repository.create(payload)
        await self._background.submit(
            IngestionJobSubmit(tenant_id=tenant_id, source_id=source.id)
        )
        return KnowledgeSourceFrontendRead.from_source(source)

    async def get_source(self, tenant_id: UUID, source_id: UUID) -> KnowledgeSourceFrontendRead:
        source = await self._require_source(tenant_id, source_id)
        return KnowledgeSourceFrontendRead.from_source(source)

    async def list_sources(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[KnowledgeSourceFrontendRead], int]:
        items, total = await self._repository.list_by_tenant(tenant_id, offset=offset, limit=limit)
        return [KnowledgeSourceFrontendRead.from_source(i) for i in items], total

    async def delete_source(self, tenant_id: UUID, source_id: UUID) -> None:
        source = await self._require_source(tenant_id, source_id)
        if self._vector_store and source.vector_namespace:
            try:
                await self._vector_store.delete_namespace(source.vector_namespace)
            except Exception:
                pass
        if source.file_path:
            await self._storage.delete(source.file_path)
        deleted = await self._repository.delete(tenant_id, source_id)
        if not deleted:
            raise NotFoundError(f"Knowledge source {source_id} not found")

    async def reprocess(
        self,
        tenant_id: UUID,
        request: KnowledgeReprocessRequest,
    ) -> list[KnowledgeSourceFrontendRead]:
        if request.source_ids:
            sources = await self._repository.list_by_ids(tenant_id, request.source_ids)
        else:
            items, _ = await self._repository.list_by_tenant(
                tenant_id,
                limit=500,
                status=KnowledgeSourceStatus.FAILED,
            )
            sources = items

        results: list[KnowledgeSourceFrontendRead] = []
        for source in sources:
            if not request.force and source.status == KnowledgeSourceStatus.READY:
                continue
            await self._repository.update_processing_state(
                tenant_id,
                source.id,
                status=KnowledgeSourceStatus.REPROCESSING,
                progress_pct=0,
                processing_error=None,
            )
            await self._background.submit_reprocess(tenant_id, source.id)
            refreshed = await self._require_source(tenant_id, source.id)
            results.append(KnowledgeSourceFrontendRead.from_source(refreshed))
        return results

    async def get_status_summary(self, tenant_id: UUID) -> KnowledgeSourceStatusSummary:
        return await self._repository.get_status_summary(tenant_id)

    async def update_source(
        self,
        tenant_id: UUID,
        source_id: UUID,
        data: KnowledgeSourceUpdate,
    ) -> KnowledgeSourceFrontendRead:
        row = await self._repository.update(tenant_id, source_id, data)
        if row is None:
            raise NotFoundError(f"Knowledge source {source_id} not found")
        return KnowledgeSourceFrontendRead.from_source(row)

    async def _require_source(self, tenant_id: UUID, source_id: UUID) -> KnowledgeSourceRead:
        row = await self._repository.get_by_id(tenant_id, source_id)
        if row is None:
            raise NotFoundError(f"Knowledge source {source_id} not found")
        return row
