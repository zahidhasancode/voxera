"""Knowledge retrieval service implementation."""

import time
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.repositories.knowledge_chunk_repository import SqlAlchemyKnowledgeChunkRepository
from app.infrastructure.repositories.knowledge_source_repository import SqlAlchemyKnowledgeSourceRepository
from app.knowledge.embeddings.provider import EmbeddingProvider
from app.knowledge.retrieval.vector_store import VectorSearchRequest, VectorStore
from app.knowledge.schemas.chunk import ChunkMetadata
from app.knowledge.schemas.retrieval import RetrievalQuery, RetrievalResult, RetrievedChunk
from app.knowledge.services.retrieval_service import RetrievalService


class RetrievalServiceImpl(RetrievalService):
    def __init__(
        self,
        source_repository: SqlAlchemyKnowledgeSourceRepository,
        chunk_repository: SqlAlchemyKnowledgeChunkRepository,
        embedding_provider: EmbeddingProvider | None,
        vector_store: VectorStore | None,
    ) -> None:
        self._sources = source_repository
        self._chunks = chunk_repository
        self._embedder = embedding_provider
        self._vector_store = vector_store

    async def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        if self._embedder is None or self._vector_store is None:
            raise NotFoundError(
                "Retrieval requires configured embedding provider and vector store"
            )

        started = time.monotonic()
        query_vector = await self._embedder.embed_query(query.query)

        namespaces: list[str] = []
        if query.source_ids:
            for source_id in query.source_ids:
                source = await self._sources.get_by_id(query.tenant_id, source_id)
                if source:
                    namespaces.append(source.vector_namespace)
        else:
            sources, _ = await self._sources.list_by_tenant(query.tenant_id, limit=500)
            namespaces = [s.vector_namespace for s in sources]

        all_results: list[RetrievedChunk] = []
        total_candidates = 0

        metadata_filter = dict(query.metadata_filter or {})
        metadata_filter["tenant_id"] = str(query.tenant_id)

        for namespace in namespaces:
            search_results = await self._vector_store.search(
                VectorSearchRequest(
                    namespace=namespace,
                    query_vector=query_vector.vector,
                    top_k=query.top_k,
                    min_score=query.min_similarity,
                    metadata_filter=metadata_filter,
                )
            )
            total_candidates += len(search_results)
            if not search_results:
                continue

            chunk_ids = [UUID(r.id) for r in search_results]
            chunks = await self._chunks.get_by_ids(query.tenant_id, chunk_ids)
            chunk_map = {str(c.id): c for c in chunks}

            for result in search_results:
                chunk = chunk_map.get(result.id)
                if chunk is None:
                    continue
                all_results.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        source_id=chunk.source_id,
                        content=chunk.content,
                        similarity_score=result.score,
                        metadata=chunk.chunk_metadata or ChunkMetadata(),
                        vector_id=chunk.vector_id,
                    )
                )

        all_results.sort(key=lambda c: c.similarity_score, reverse=True)
        top_chunks = all_results[: query.top_k]
        elapsed_ms = int((time.monotonic() - started) * 1000)

        return RetrievalResult(
            tenant_id=query.tenant_id,
            query=query.query,
            chunks=top_chunks,
            total_candidates=total_candidates,
            retrieval_time_ms=elapsed_ms,
        )
