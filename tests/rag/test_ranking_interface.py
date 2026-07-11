"""Unit tests for ranking strategy interfaces."""

import pytest
from uuid import uuid4

from app.core.exceptions import NotFoundError
from app.rag.interfaces.models import RankedChunk, RankingStrategyType, RetrievalRequest
from app.rag.ranking.strategies import (
    CosineSimilarityRankingStrategy,
    HybridSearchRankingStrategy,
    KeywordBoostRankingStrategy,
    MaxMarginalRelevanceStrategy,
    RankingStrategyRegistry,
    ReciprocalRankFusionStrategy,
    SemanticRerankingStrategy,
)


@pytest.fixture
def tenant_id():
    return uuid4()


def _chunks():
    return [
        RankedChunk(
            chunk_id=uuid4(),
            source_id=uuid4(),
            tenant_id=uuid4(),
            content=f"chunk {i}",
            score=0.5 + i * 0.1,
            rank=0,
        )
        for i in range(3)
    ]


@pytest.mark.asyncio
async def test_cosine_similarity_ranks_by_score(tenant_id):
    strategy = CosineSimilarityRankingStrategy()
    request = RetrievalRequest(tenant_id=tenant_id, query="test")
    ranked = await strategy.rank(_chunks(), request)

    assert ranked[0].score >= ranked[1].score >= ranked[2].score
    assert ranked[0].rank == 0
    assert ranked[2].rank == 2
    assert strategy.strategy_type == RankingStrategyType.COSINE_SIMILARITY


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strategy_cls",
    [
        HybridSearchRankingStrategy,
        KeywordBoostRankingStrategy,
        SemanticRerankingStrategy,
        ReciprocalRankFusionStrategy,
        MaxMarginalRelevanceStrategy,
    ],
)
async def test_future_rankers_raise_not_implemented(strategy_cls, tenant_id):
    strategy = strategy_cls()
    request = RetrievalRequest(tenant_id=tenant_id, query="test")
    with pytest.raises(NotImplementedError):
        await strategy.rank(_chunks(), request)


def test_ranking_registry_resolves_cosine(tenant_id):
    registry = RankingStrategyRegistry()
    registry.register(CosineSimilarityRankingStrategy())
    strategy = registry.resolve(RankingStrategyType.COSINE_SIMILARITY)
    assert isinstance(strategy, CosineSimilarityRankingStrategy)


def test_ranking_registry_raises_for_unknown():
    registry = RankingStrategyRegistry()
    with pytest.raises(NotFoundError):
        registry.resolve(RankingStrategyType.HYBRID)
