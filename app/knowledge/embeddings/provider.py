"""Embedding provider abstraction."""

from abc import ABC, abstractmethod

from pydantic import Field

from app.core.schemas import SchemaBase


class EmbeddingVector(SchemaBase):
    vector: list[float]
    model: str
    dimensions: int
    token_count: int | None = None


class EmbeddingBatch(SchemaBase):
    vectors: list[EmbeddingVector]
    model: str


class EmbeddingProvider(ABC):
    """Port for document and query embedding — provider-agnostic."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> EmbeddingBatch:
        """Embed multiple document chunks (batch-optimized)."""
        raise NotImplementedError

    @abstractmethod
    async def embed_query(self, query: str) -> EmbeddingVector:
        """Embed a single retrieval query."""
        raise NotImplementedError

    async def embed_document(self, text: str) -> EmbeddingVector:
        """Convenience wrapper for single-document embedding."""
        batch = await self.embed_documents([text])
        return batch.vectors[0]


class EmbeddingRequest(SchemaBase):
    texts: list[str] = Field(..., min_length=1)
    input_type: str = Field(default="document", pattern="^(document|query)$")
