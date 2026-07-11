"""Ranking strategy abstraction — provider-agnostic."""

from abc import ABC, abstractmethod

from app.core.exceptions import NotFoundError
from app.rag.interfaces.models import RankedChunk, RankingStrategyType, RetrievalRequest


class RankingStrategy(ABC):
    """Port for re-ranking retrieved chunks."""

    @property
    @abstractmethod
    def strategy_type(self) -> RankingStrategyType:
        raise NotImplementedError

    @abstractmethod
    async def rank(
        self,
        chunks: list[RankedChunk],
        request: RetrievalRequest,
    ) -> list[RankedChunk]:
        raise NotImplementedError


class CosineSimilarityRankingStrategy(RankingStrategy):
    """Default pass-through ranker using vector-store cosine scores."""

    @property
    def strategy_type(self) -> RankingStrategyType:
        return RankingStrategyType.COSINE_SIMILARITY

    async def rank(
        self,
        chunks: list[RankedChunk],
        request: RetrievalRequest,
    ) -> list[RankedChunk]:
        sorted_chunks = sorted(chunks, key=lambda c: c.score, reverse=True)
        return [
            chunk.model_copy(update={"rank": idx})
            for idx, chunk in enumerate(sorted_chunks)
        ]


class HybridSearchRankingStrategy(RankingStrategy):
    """Hybrid dense + sparse search — implement in infrastructure sprint."""

    @property
    def strategy_type(self) -> RankingStrategyType:
        return RankingStrategyType.HYBRID

    async def rank(
        self,
        chunks: list[RankedChunk],
        request: RetrievalRequest,
    ) -> list[RankedChunk]:
        raise NotImplementedError("HybridSearchRankingStrategy requires infrastructure implementation")


class KeywordBoostRankingStrategy(RankingStrategy):
    @property
    def strategy_type(self) -> RankingStrategyType:
        return RankingStrategyType.KEYWORD_BOOST

    async def rank(
        self,
        chunks: list[RankedChunk],
        request: RetrievalRequest,
    ) -> list[RankedChunk]:
        raise NotImplementedError("KeywordBoostRankingStrategy requires infrastructure implementation")


class SemanticRerankingStrategy(RankingStrategy):
    @property
    def strategy_type(self) -> RankingStrategyType:
        return RankingStrategyType.SEMANTIC_RERANK

    async def rank(
        self,
        chunks: list[RankedChunk],
        request: RetrievalRequest,
    ) -> list[RankedChunk]:
        raise NotImplementedError("SemanticRerankingStrategy requires cross-encoder implementation")


class ReciprocalRankFusionStrategy(RankingStrategy):
    @property
    def strategy_type(self) -> RankingStrategyType:
        return RankingStrategyType.RECIPROCAL_RANK_FUSION

    async def rank(
        self,
        chunks: list[RankedChunk],
        request: RetrievalRequest,
    ) -> list[RankedChunk]:
        raise NotImplementedError("ReciprocalRankFusionStrategy requires multi-index implementation")


class MaxMarginalRelevanceStrategy(RankingStrategy):
    @property
    def strategy_type(self) -> RankingStrategyType:
        return RankingStrategyType.MMR

    async def rank(
        self,
        chunks: list[RankedChunk],
        request: RetrievalRequest,
    ) -> list[RankedChunk]:
        raise NotImplementedError("MaxMarginalRelevanceStrategy requires embedding similarity implementation")


class RankingStrategyRegistry:
    """Resolves ranking strategy by type."""

    def __init__(self) -> None:
        self._strategies: dict[RankingStrategyType, RankingStrategy] = {}

    def register(self, strategy: RankingStrategy) -> None:
        self._strategies[strategy.strategy_type] = strategy

    def resolve(self, strategy_type: RankingStrategyType) -> RankingStrategy:
        strategy = self._strategies.get(strategy_type)
        if strategy is None:
            raise NotFoundError(f"Ranking strategy not registered: {strategy_type.value}")
        return strategy
