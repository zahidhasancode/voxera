"""Unit tests for EnterpriseRetriever with mocked dependencies."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.core.enums import KnowledgeSourceStatus
from app.knowledge.embeddings.provider import EmbeddingVector
from app.knowledge.schemas.source import KnowledgeSourceRead
from app.rag.cache.base import InMemoryRetrievalCache
from app.rag.interfaces.models import RetrievalRequest
from app.rag.ranking.strategies import CosineSimilarityRankingStrategy, RankingStrategyRegistry
from app.rag.retriever.enterprise_retriever import EnterpriseRetrieverImpl
from app.rag.retriever.language_detector import HeuristicLanguageDetector


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def source_id():
    return uuid4()


def _source_read(tenant_id, source_id):
    from datetime import datetime, timezone

    from app.core.enums import KnowledgeEmbeddingStatus, KnowledgeProcessingStage, KnowledgeSourceType

    return KnowledgeSourceRead(
        id=source_id,
        tenant_id=tenant_id,
        title="FAQ",
        source_type=KnowledgeSourceType.TXT,
        status=KnowledgeSourceStatus.READY,
        file_path="/tmp/faq.txt",
        website_url=None,
        file_size_bytes=100,
        content_type="text/plain",
        original_filename="faq.txt",
        processing_stage=KnowledgeProcessingStage.COMPLETE,
        processing_started_at=None,
        processing_completed_at=None,
        processing_error=None,
        progress_pct=100,
        chunk_count=1,
        embedding_count=1,
        embedding_model="test",
        embedding_status=KnowledgeEmbeddingStatus.COMPLETE,
        vector_namespace=f"tenant-{tenant_id}-source-{source_id}",
        vector_store_type=None,
        chunk_config=None,
        metadata=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_retriever_returns_ranked_chunks(tenant_id, source_id):
    chunk_id = uuid4()
    source = _source_read(tenant_id, source_id)

    source_repo = AsyncMock()
    source_repo.list_by_tenant = AsyncMock(return_value=([source], 1))

    chunk_read = MagicMock()
    chunk_read.id = chunk_id
    chunk_read.source_id = source_id
    chunk_read.content = "Our refund window is 30 days."
    chunk_read.chunk_metadata = MagicMock()
    chunk_read.chunk_metadata.model_dump = MagicMock(return_value={"document": "faq.txt", "language": "en"})
    chunk_read.vector_id = "vec-1"

    chunk_repo = AsyncMock()
    chunk_repo.get_by_ids = AsyncMock(return_value=[chunk_read])

    embedder = AsyncMock()
    embedder.embed_query = AsyncMock(
        return_value=EmbeddingVector(vector=[0.1, 0.2, 0.3], model="test", dimensions=3)
    )

    vector_result = MagicMock()
    vector_result.id = str(chunk_id)
    vector_result.score = 0.91
    vector_result.metadata = {}

    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=[vector_result])

    agent_scope = AsyncMock()
    agent_scope.resolve_source_ids = AsyncMock(return_value=None)

    registry = RankingStrategyRegistry()
    registry.register(CosineSimilarityRankingStrategy())

    retriever = EnterpriseRetrieverImpl(
        source_repository=source_repo,
        chunk_repository=chunk_repo,
        embedding_provider=embedder,
        vector_store=vector_store,
        agent_scope=agent_scope,
        ranking_registry=registry,
        cache=InMemoryRetrievalCache(),
        language_detector=HeuristicLanguageDetector(),
    )

    response = await retriever.retrieve_by_tenant(
        tenant_id,
        "What is the refund policy?",
        top_k=5,
        min_similarity=0.5,
    )

    assert response.tenant_id == tenant_id
    assert len(response.chunks) == 1
    assert response.chunks[0].score == 0.91
    assert response.query.language == "en"
    embedder.embed_query.assert_awaited_once()
    vector_store.search.assert_awaited()


@pytest.mark.asyncio
async def test_retriever_cache_hit_skips_embed(tenant_id, source_id):
    source = _source_read(tenant_id, source_id)
    source_repo = AsyncMock()
    source_repo.list_by_tenant = AsyncMock(return_value=([source], 1))
    chunk_repo = AsyncMock()
    chunk_repo.get_by_ids = AsyncMock(return_value=[])

    embedder = AsyncMock()
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=[])

    registry = RankingStrategyRegistry()
    registry.register(CosineSimilarityRankingStrategy())

    retriever = EnterpriseRetrieverImpl(
        source_repository=source_repo,
        chunk_repository=chunk_repo,
        embedding_provider=embedder,
        vector_store=vector_store,
        agent_scope=AsyncMock(),
        ranking_registry=registry,
        cache=InMemoryRetrievalCache(),
        language_detector=HeuristicLanguageDetector(),
    )

    request = RetrievalRequest(tenant_id=tenant_id, query="cached query", min_similarity=0.0)
    await retriever.retrieve(request)
    await retriever.retrieve(request)

    assert embedder.embed_query.await_count == 1
