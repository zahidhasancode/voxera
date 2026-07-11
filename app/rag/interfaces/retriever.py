"""Enterprise retriever port."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.rag.interfaces.models import MetadataFilterSpec, RankedChunk, RetrievalRequest, RetrievalResponse


class EnterpriseRetriever(ABC):
    """
    Core retrieval port for tenant-scoped knowledge search.

    All methods enforce tenant isolation at the repository and vector-store layers.
    """

    @abstractmethod
    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    async def retrieve_by_tenant(
        self,
        tenant_id: UUID,
        query: str,
        *,
        top_k: int | None = None,
        min_similarity: float | None = None,
        metadata_filter: MetadataFilterSpec | None = None,
    ) -> RetrievalResponse:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @staticmethod
    def chunks_to_ranked(chunks: list[RankedChunk]) -> list[RankedChunk]:
        return sorted(chunks, key=lambda c: c.score, reverse=True)
