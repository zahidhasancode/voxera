"""Knowledge chunk Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.core.schemas import SchemaBase, TenantScopedSchema, TimestampSchema


class ChunkMetadata(SchemaBase):
    document: str | None = None
    page: int | None = None
    section: str | None = None
    chunk_number: int | None = None
    language: str | None = None
    source: str | None = None
    extra: dict | None = None


class KnowledgeChunkCreate(TenantScopedSchema):
    source_id: UUID
    chunk_number: int = Field(..., ge=0)
    content: str = Field(..., min_length=1)
    token_count: int | None = Field(default=None, ge=0)
    char_count: int | None = Field(default=None, ge=0)
    vector_id: str | None = None
    chunk_metadata: ChunkMetadata | None = None


class KnowledgeChunkRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    source_id: UUID
    chunk_number: int
    content: str
    token_count: int | None
    char_count: int | None
    vector_id: str | None
    chunk_metadata: ChunkMetadata | None
