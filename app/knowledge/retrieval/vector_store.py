"""Vector store abstraction."""

from abc import ABC, abstractmethod
from uuid import UUID

from pydantic import Field

from app.core.schemas import SchemaBase


class VectorRecord(SchemaBase):
    id: str
    vector: list[float]
    metadata: dict = Field(default_factory=dict)


class VectorSearchResult(SchemaBase):
    id: str
    score: float = Field(..., ge=0.0)
    metadata: dict = Field(default_factory=dict)


class VectorSearchRequest(SchemaBase):
    namespace: str
    query_vector: list[float]
    top_k: int = Field(default=5, ge=1, le=100)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata_filter: dict | None = None


class VectorStore(ABC):
    """Port for vector storage and similarity search — provider-agnostic."""

    @property
    @abstractmethod
    def store_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def create_namespace(self, namespace: str, *, dimensions: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def insert(self, namespace: str, records: list[VectorRecord]) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, namespace: str, ids: list[str]) -> int:
        raise NotImplementedError

    @abstractmethod
    async def search(self, request: VectorSearchRequest) -> list[VectorSearchResult]:
        raise NotImplementedError

    @abstractmethod
    async def delete_namespace(self, namespace: str) -> None:
        raise NotImplementedError

    @staticmethod
    def build_tenant_namespace(tenant_id: UUID, source_id: UUID) -> str:
        """Deterministic, tenant-isolated namespace (no shared namespaces)."""
        return f"tenant-{tenant_id}-source-{source_id}"
