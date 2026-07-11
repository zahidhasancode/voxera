"""Unconfigured provider stubs — raise clear errors until Sprint wiring."""

from app.core.exceptions import DatabaseUnavailableError
from app.knowledge.embeddings.provider import EmbeddingBatch, EmbeddingProvider, EmbeddingVector
from app.knowledge.retrieval.vector_store import VectorRecord, VectorSearchRequest, VectorSearchResult, VectorStore


class UnconfiguredEmbeddingProvider(EmbeddingProvider):
    """Placeholder until an embedding provider is registered via DI."""

    def __init__(self, provider_name: str = "unconfigured") -> None:
        self._provider_name = provider_name

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return "unconfigured"

    async def embed_documents(self, texts: list[str]) -> EmbeddingBatch:
        raise DatabaseUnavailableError(
            "Embedding provider not configured. Set KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER and register a provider."
        )

    async def embed_query(self, query: str) -> EmbeddingVector:
        raise DatabaseUnavailableError(
            "Embedding provider not configured. Set KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER and register a provider."
        )


class UnconfiguredVectorStore(VectorStore):
    """Placeholder until a vector store is registered via DI."""

    def __init__(self, store_name: str = "unconfigured") -> None:
        self._store_name = store_name

    @property
    def store_name(self) -> str:
        return self._store_name

    async def create_namespace(self, namespace: str, *, dimensions: int) -> None:
        raise DatabaseUnavailableError(
            "Vector store not configured. Set KNOWLEDGE_DEFAULT_VECTOR_STORE and register a store."
        )

    async def insert(self, namespace: str, records: list[VectorRecord]) -> list[str]:
        raise DatabaseUnavailableError("Vector store not configured.")

    async def delete(self, namespace: str, ids: list[str]) -> int:
        raise DatabaseUnavailableError("Vector store not configured.")

    async def search(self, request: VectorSearchRequest) -> list[VectorSearchResult]:
        raise DatabaseUnavailableError("Vector store not configured.")

    async def delete_namespace(self, namespace: str) -> None:
        raise DatabaseUnavailableError("Vector store not configured.")
