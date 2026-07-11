"""Knowledge ingestion service implementation."""

from datetime import datetime, timezone
from uuid import UUID

from app.infrastructure.knowledge.parser_factory import build_parser_registry
from app.infrastructure.repositories.knowledge_chunk_repository import SqlAlchemyKnowledgeChunkRepository
from app.infrastructure.repositories.knowledge_source_repository import SqlAlchemyKnowledgeSourceRepository
from app.core.enums import KnowledgeIngestionJobStatus, KnowledgeProcessingStage
from app.knowledge.embeddings.provider import EmbeddingProvider
from app.knowledge.ingestion.pipeline import IngestionPipeline
from app.knowledge.retrieval.vector_store import VectorStore
from app.knowledge.schemas.ingestion import IngestionJobStatus, IngestionJobSubmit
from app.knowledge.services.ingestion_service import KnowledgeIngestionService


class KnowledgeIngestionServiceImpl(KnowledgeIngestionService):
    def __init__(
        self,
        source_repository: SqlAlchemyKnowledgeSourceRepository,
        chunk_repository: SqlAlchemyKnowledgeChunkRepository,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
        background_processor=None,
    ) -> None:
        self._sources = source_repository
        self._chunks = chunk_repository
        self._embedder = embedding_provider
        self._vector_store = vector_store
        self._background = background_processor
        self._parser_registry = build_parser_registry()

    def _pipeline(self) -> IngestionPipeline:
        return IngestionPipeline(
            source_repository=self._sources,
            chunk_repository=self._chunks,
            parser_registry=self._parser_registry,
            embedding_provider=self._embedder,
            vector_store=self._vector_store,
        )

    async def enqueue_processing(self, tenant_id: UUID, source_id: UUID) -> IngestionJobStatus:
        if self._background is None:
            await self.run_processing(tenant_id, source_id)
            now = datetime.now(timezone.utc)
            return IngestionJobStatus(
                job_id="sync",
                source_id=source_id,
                tenant_id=tenant_id,
                status=KnowledgeIngestionJobStatus.COMPLETED,
                stage=KnowledgeProcessingStage.COMPLETE,
                progress_pct=100,
                submitted_at=now,
                completed_at=now,
            )
        return await self._background.submit(
            IngestionJobSubmit(tenant_id=tenant_id, source_id=source_id)
        )

    async def run_processing(self, tenant_id: UUID, source_id: UUID) -> None:
        await self._pipeline().run(tenant_id, source_id)
