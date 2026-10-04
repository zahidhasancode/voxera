"""Enterprise retriever implementation."""

import time
from uuid import UUID

from app.core.config import settings
from app.core.enums import KnowledgeSourceStatus
from app.core.exceptions import DatabaseUnavailableError, NotFoundError
from app.knowledge.embeddings.provider import EmbeddingProvider
from app.knowledge.repository.chunk_repository import KnowledgeChunkRepository
from app.knowledge.repository.source_repository import KnowledgeSourceRepository
from app.knowledge.retrieval.vector_store import VectorSearchRequest, VectorStore
from app.rag.cache.base import RetrievalCache
from app.rag.interfaces.agent_scope import AgentKnowledgeScope
from app.rag.interfaces.models import (
    MetadataFilterSpec,
    RankedChunk,
    RetrievalRequest,
    RetrievalResponse,
)
from app.rag.interfaces.retriever import EnterpriseRetriever
from app.rag.ranking.strategies import RankingStrategyRegistry
from app.rag.retriever.language_detector import HeuristicLanguageDetector, LanguageDetector
from app.rag.retriever.normalizer import QueryNormalizer


class EnterpriseRetrieverImpl(EnterpriseRetriever):
    """Production retriever with tenant isolation, caching, and ranking."""

    def __init__(
        self,
        *,
        source_repository: KnowledgeSourceRepository,
        chunk_repository: KnowledgeChunkRepository,
        embedding_provider: EmbeddingProvider | None,
        vector_store: VectorStore | None,
        agent_scope: AgentKnowledgeScope,
        ranking_registry: RankingStrategyRegistry,
        cache: RetrievalCache,
        language_detector: LanguageDetector | None = None,
        query_normalizer: QueryNormalizer | None = None,
    ) -> None:
        self._sources = source_repository
        self._chunks = chunk_repository
        self._embedder = embedding_provider
        self._vector_store = vector_store
        self._agent_scope = agent_scope
        self._ranking = ranking_registry
        self._cache = cache
        self._language_detector = language_detector or HeuristicLanguageDetector()
        self._normalizer = query_normalizer or QueryNormalizer()

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        return await self._execute(request)

    async def retrieve_by_agent(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        query: str,
        *,
        top_k: int | None = None,
        min_similarity: float | None = None,
        metadata_filter: MetadataFilterSpec | None = None,
    ) -> RetrievalResponse:
        request = RetrievalRequest(
            tenant_id=tenant_id,
            agent_id=agent_id,
            query=query,
            top_k=top_k,
            min_similarity=min_similarity,
            metadata_filter=metadata_filter,
        )
        return await self._execute(request)

    async def retrieve_by_tenant(
        self,
        tenant_id: UUID,
        query: str,
        *,
        top_k: int | None = None,
        min_similarity: float | None = None,
        metadata_filter: MetadataFilterSpec | None = None,
    ) -> RetrievalResponse:
        request = RetrievalRequest(
            tenant_id=tenant_id,
            query=query,
            top_k=top_k,
            min_similarity=min_similarity,
            metadata_filter=metadata_filter,
        )
        return await self._execute(request)

    async def retrieve_with_filters(
        self,
        tenant_id: UUID,
        query: str,
        filters: MetadataFilterSpec,
        *,
        agent_id: UUID | None = None,
        top_k: int | None = None,
        min_similarity: float | None = None,
    ) -> RetrievalResponse:
        request = RetrievalRequest(
            tenant_id=tenant_id,
            agent_id=agent_id,
            query=query,
            top_k=top_k,
            min_similarity=min_similarity,
            metadata_filter=filters,
        )
        return await self._execute(request)

    async def _execute(self, request: RetrievalRequest) -> RetrievalResponse:
        if self._embedder is None or self._vector_store is None:
            raise DatabaseUnavailableError(
                "Retrieval engine requires configured embedding provider and vector store"
            )

        started = time.monotonic()
        cache_namespace = f"tenant-{request.tenant_id}"
        cache_key = RetrievalCache.build_key(
            request.model_dump(mode="json", exclude={"conversation", "include_prompt"}),
        )

        if settings.RAG_ENABLE_RETRIEVAL_CACHE:
            cached = await self._cache.get(cache_namespace, cache_key)
            if cached is not None:
                return cached.model_copy(update={"cache_hit": True})

        lang_result = await self._language_detector.detect(request.query)
        normalized = self._normalizer.normalize(
            request.query,
            detected_language=lang_result.language,
        )
        normalized = normalized.model_copy(
            update={"language_confidence": lang_result.confidence}
        )

        embed_started = time.monotonic()
        embed_cache_key = RetrievalCache.build_key("embed", normalized.normalized)
        query_vector = await self._cache.get(cache_namespace, embed_cache_key)
        if query_vector is None:
            embedding = await self._embedder.embed_query(normalized.normalized)
            query_vector = embedding.vector
            await self._cache.set(
                cache_namespace,
                embed_cache_key,
                query_vector,
                ttl_seconds=settings.RAG_EMBEDDING_CACHE_TTL_SECONDS,
            )
        embedding_latency_ms = int((time.monotonic() - embed_started) * 1000)

        source_ids = await self._resolve_source_ids(request)
        namespaces, source_map = await self._resolve_namespaces(request.tenant_id, source_ids)

        top_k = request.top_k or settings.RAG_DEFAULT_TOP_K
        min_sim = request.min_similarity or settings.RAG_MIN_SIMILARITY_THRESHOLD
        metadata_filter = self._build_metadata_filter(request)

        candidates: list[RankedChunk] = []
        total_candidates = 0

        for namespace in namespaces:
            results = await self._vector_store.search(
                VectorSearchRequest(
                    namespace=namespace,
                    query_vector=query_vector,
                    top_k=top_k * 2,
                    min_score=min_sim,
                    metadata_filter=metadata_filter,
                )
            )
            total_candidates += len(results)
            if not results:
                continue

            chunk_ids = [UUID(r.id) for r in results]
            chunks = await self._chunks.get_by_ids(request.tenant_id, chunk_ids)
            chunk_map = {str(c.id): c for c in chunks}

            for result in results:
                chunk = chunk_map.get(result.id)
                if chunk is None:
                    continue
                source = source_map.get(chunk.source_id)
                meta = chunk.chunk_metadata.model_dump() if chunk.chunk_metadata else {}
                candidates.append(
                    RankedChunk(
                        chunk_id=chunk.id,
                        source_id=chunk.source_id,
                        tenant_id=request.tenant_id,
                        content=chunk.content,
                        score=result.score,
                        rank=0,
                        metadata=meta,
                        source_title=source.title if source else None,
                        document=meta.get("document"),
                        page=meta.get("page"),
                        language=meta.get("language"),
                        vector_id=chunk.vector_id,
                    )
                )

        rank_started = time.monotonic()
        ranker = self._ranking.resolve(request.ranking_strategy)
        ranked = await ranker.rank(candidates, request)
        ranked = ranked[:top_k]
        ranking_latency_ms = int((time.monotonic() - rank_started) * 1000)

        avg_sim = sum(c.score for c in ranked) / len(ranked) if ranked else 0.0
        retrieval_latency_ms = int((time.monotonic() - started) * 1000)

        response = RetrievalResponse(
            tenant_id=request.tenant_id,
            agent_id=request.agent_id,
            query=normalized,
            chunks=ranked,
            total_candidates=total_candidates,
            average_similarity=avg_sim,
            retrieval_latency_ms=retrieval_latency_ms,
            embedding_latency_ms=embedding_latency_ms,
            ranking_latency_ms=ranking_latency_ms,
            cache_hit=False,
        )

        if settings.RAG_ENABLE_RETRIEVAL_CACHE:
            await self._cache.set(
                cache_namespace,
                cache_key,
                response,
                ttl_seconds=settings.RAG_CACHE_TTL_SECONDS,
            )

        return response

    async def _resolve_source_ids(self, request: RetrievalRequest) -> list[UUID] | None:
        if request.source_ids:
            return request.source_ids
        if request.agent_id:
            return await self._agent_scope.resolve_source_ids(
                request.tenant_id,
                request.agent_id,
            )
        return None

    async def _resolve_namespaces(
        self,
        tenant_id: UUID,
        source_ids: list[UUID] | None,
    ) -> tuple[list[str], dict]:
        if source_ids:
            sources = await self._sources.list_by_ids(tenant_id, source_ids)
        else:
            sources, _ = await self._sources.list_by_tenant(
                tenant_id,
                limit=1000,
                status=KnowledgeSourceStatus.READY,
            )

        active = [s for s in sources if s.status == KnowledgeSourceStatus.READY]
        if not active:
            raise NotFoundError("No active knowledge sources available for retrieval")

        source_map = {s.id: s for s in active}
        namespaces = [s.vector_namespace for s in active]
        return namespaces, source_map

    @staticmethod
    def _build_metadata_filter(request: RetrievalRequest) -> dict:
        filters = {"tenant_id": str(request.tenant_id)}
        if request.metadata_filter:
            filters.update(request.metadata_filter.to_filter_dict())
        return filters
