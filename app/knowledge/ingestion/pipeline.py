"""Knowledge ingestion pipeline orchestrator."""

from datetime import datetime, timezone
from uuid import UUID

from app.core.enums import (
    KnowledgeEmbeddingStatus,
    KnowledgeProcessingStage,
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)
from app.core.exceptions import NotFoundError
from app.core.logger import get_logger
from app.knowledge.chunking.strategy import ChunkingStrategy
from app.knowledge.embeddings.provider import EmbeddingProvider
from app.knowledge.ingestion.metrics import ProcessingMetricsCollector
from app.knowledge.ingestion.stages import clean_text, progress_for_stage
from app.knowledge.parser.registry import ParserRegistry
from app.knowledge.repository.chunk_repository import KnowledgeChunkRepository
from app.knowledge.repository.source_repository import KnowledgeSourceRepository
from app.knowledge.retrieval.vector_store import VectorRecord, VectorStore
from app.knowledge.schemas.chunk import ChunkMetadata, KnowledgeChunkCreate

logger = get_logger(__name__)


class IngestionPipeline:
    """
    Orchestrates: Upload → Parse → Clean → Chunk → Metadata → Embed → Vector Store.

    Depends on injected abstractions only — no provider-specific code.
    """

    def __init__(
        self,
        *,
        source_repository: KnowledgeSourceRepository,
        chunk_repository: KnowledgeChunkRepository,
        parser_registry: ParserRegistry,
        embedding_provider: EmbeddingProvider | None,
        vector_store: VectorStore | None,
    ) -> None:
        self._sources = source_repository
        self._chunks = chunk_repository
        self._parsers = parser_registry
        self._embedder = embedding_provider
        self._vector_store = vector_store

    async def run(self, tenant_id: UUID, source_id: UUID) -> None:
        source = await self._sources.get_by_id(tenant_id, source_id)
        if source is None:
            raise NotFoundError(f"Knowledge source {source_id} not found")

        metrics = ProcessingMetricsCollector(tenant_id, source_id)
        await self._sources.update_processing_state(
            tenant_id,
            source_id,
            status=KnowledgeSourceStatus.PROCESSING,
            stage=KnowledgeProcessingStage.PARSE,
            progress_pct=progress_for_stage(KnowledgeProcessingStage.PARSE),
            processing_started_at=datetime.now(timezone.utc),
            processing_error=None,
        )

        try:
            with metrics.stage(KnowledgeProcessingStage.PARSE.value):
                parsed = await self._parse(source)

            with metrics.stage(KnowledgeProcessingStage.CLEAN.value):
                cleaned = clean_text(parsed.text)

            chunk_config = source.chunk_config
            chunker = ChunkingStrategy(chunk_config)
            with metrics.stage(KnowledgeProcessingStage.CHUNK.value):
                await self._sources.update_processing_state(
                    tenant_id,
                    source_id,
                    stage=KnowledgeProcessingStage.CHUNK,
                    progress_pct=progress_for_stage(KnowledgeProcessingStage.CHUNK),
                )
                text_chunks = chunker.chunk_text(
                    cleaned,
                    base_metadata={
                        "document": source.title,
                        "language": parsed.language,
                        "source": source.source_type.value,
                    },
                )
                metrics.record_chunks(text_chunks)
                await self._chunks.delete_by_source(tenant_id, source_id)
                db_chunks = await self._persist_chunks(tenant_id, source_id, text_chunks)

            with metrics.stage(KnowledgeProcessingStage.METADATA.value):
                await self._sources.update_processing_state(
                    tenant_id,
                    source_id,
                    stage=KnowledgeProcessingStage.METADATA,
                    progress_pct=progress_for_stage(KnowledgeProcessingStage.METADATA),
                    chunk_count=len(db_chunks),
                )

            vector_ids: list[str] = []
            if self._embedder and self._vector_store:
                with metrics.stage(KnowledgeProcessingStage.EMBED.value):
                    await self._sources.update_processing_state(
                        tenant_id,
                        source_id,
                        stage=KnowledgeProcessingStage.EMBED,
                        progress_pct=progress_for_stage(KnowledgeProcessingStage.EMBED),
                        embedding_status=KnowledgeEmbeddingStatus.IN_PROGRESS,
                    )
                    texts = [c.content for c in db_chunks]
                    batch = await self._embedder.embed_documents(texts)
                    metrics.record_embeddings(len(batch.vectors))

                with metrics.stage(KnowledgeProcessingStage.VECTOR_STORE.value):
                    await self._sources.update_processing_state(
                        tenant_id,
                        source_id,
                        stage=KnowledgeProcessingStage.VECTOR_STORE,
                        progress_pct=progress_for_stage(KnowledgeProcessingStage.VECTOR_STORE),
                    )
                    logger.info(
                        "Vector insert started",
                        extra_fields={
                            "tenant_id": str(tenant_id),
                            "source_id": str(source_id),
                            "namespace": source.vector_namespace,
                            "event": "knowledge_vector_insert_started",
                        },
                    )
                    dimensions = batch.vectors[0].dimensions if batch.vectors else 0
                    await self._vector_store.create_namespace(source.vector_namespace, dimensions=dimensions)
                    records = [
                        VectorRecord(
                            id=str(chunk.id),
                            vector=batch.vectors[i].vector,
                            metadata={
                                "tenant_id": str(tenant_id),
                                "source_id": str(source_id),
                                "chunk_number": chunk.chunk_number,
                                **(chunk.chunk_metadata.model_dump() if chunk.chunk_metadata else {}),
                            },
                        )
                        for i, chunk in enumerate(db_chunks)
                    ]
                    vector_ids = await self._vector_store.insert(source.vector_namespace, records)
                    await self._chunks.update_vector_ids(
                        tenant_id,
                        {str(c.id): vector_ids[i] for i, c in enumerate(db_chunks)},
                    )
            else:
                await self._sources.update_processing_state(
                    tenant_id,
                    source_id,
                    embedding_status=KnowledgeEmbeddingStatus.SKIPPED,
                )

            await self._sources.update_processing_state(
                tenant_id,
                source_id,
                status=KnowledgeSourceStatus.READY,
                stage=KnowledgeProcessingStage.COMPLETE,
                progress_pct=100,
                processing_completed_at=datetime.now(timezone.utc),
                chunk_count=len(db_chunks),
                embedding_count=len(vector_ids),
                embedding_status=(
                    KnowledgeEmbeddingStatus.COMPLETE
                    if vector_ids
                    else KnowledgeEmbeddingStatus.SKIPPED
                ),
            )
            metrics.snapshot()

        except Exception as exc:
            await self._sources.update_processing_state(
                tenant_id,
                source_id,
                status=KnowledgeSourceStatus.FAILED,
                stage=KnowledgeProcessingStage.FAILED,
                progress_pct=0,
                processing_error=str(exc),
                processing_completed_at=datetime.now(timezone.utc),
                embedding_status=KnowledgeEmbeddingStatus.FAILED,
            )
            logger.error(
                "Knowledge processing failed",
                extra_fields={
                    "tenant_id": str(tenant_id),
                    "source_id": str(source_id),
                    "error": str(exc),
                    "event": "knowledge_processing_failed",
                },
            )
            raise

    async def _parse(self, source):
        parser = self._parsers.resolve(source.source_type)
        if source.source_type == KnowledgeSourceType.WEBSITE:
            if not source.website_url:
                raise ValueError("website_url required for website sources")
            return await parser.parse_url(source.website_url)
        if not source.file_path:
            raise ValueError("file_path required for file-based sources")
        return await parser.parse_file(source.file_path, source_type=source.source_type)

    async def _persist_chunks(self, tenant_id: UUID, source_id: UUID, text_chunks: list):
        creates = [
            KnowledgeChunkCreate(
                tenant_id=tenant_id,
                source_id=source_id,
                chunk_number=tc.chunk_number,
                content=tc.content,
                char_count=tc.char_count,
                token_count=tc.token_count,
                chunk_metadata=ChunkMetadata(**(tc.metadata or {})),
            )
            for tc in text_chunks
        ]
        return await self._chunks.create_batch(creates)
