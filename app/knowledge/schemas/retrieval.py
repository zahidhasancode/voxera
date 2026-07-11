"""Retrieval Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.core.schemas import SchemaBase
from app.knowledge.schemas.chunk import ChunkMetadata


class RetrievalQuery(SchemaBase):
    tenant_id: UUID
    agent_id: UUID | None = None
    query: str = Field(..., min_length=1, max_length=8192)
    top_k: int = Field(default=5, ge=1, le=100)
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata_filter: dict | None = Field(
        default=None,
        description="Key-value filters applied to chunk metadata",
    )
    source_ids: list[UUID] | None = Field(
        default=None,
        description="Restrict search to specific knowledge sources",
    )


class RetrievedChunk(SchemaBase):
    chunk_id: UUID
    source_id: UUID
    content: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    metadata: ChunkMetadata | None = None
    vector_id: str | None = None


class RetrievalResult(SchemaBase):
    tenant_id: UUID
    query: str
    chunks: list[RetrievedChunk]
    total_candidates: int
    retrieval_time_ms: int | None = None
