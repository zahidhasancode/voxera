"""Knowledge source Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, HttpUrl

from app.core.enums import (
    KnowledgeEmbeddingStatus,
    KnowledgeProcessingStage,
    KnowledgeSourceStatus,
    KnowledgeSourceType,
    VectorStoreType,
)
from app.core.schemas import SchemaBase, TenantScopedSchema, TimestampSchema
from app.knowledge.chunking.models import ChunkConfig


class KnowledgeSourceCreate(TenantScopedSchema):
    title: str = Field(..., min_length=1, max_length=512)
    source_type: KnowledgeSourceType
    website_url: HttpUrl | None = None
    chunk_config: ChunkConfig | None = None
    embedding_model: str | None = Field(default=None, max_length=128)
    vector_store_type: VectorStoreType | None = None
    metadata: dict | None = None


class KnowledgeSourceUpdate(SchemaBase):
    title: str | None = Field(default=None, min_length=1, max_length=512)
    metadata: dict | None = None


class KnowledgeSourceRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    title: str
    source_type: KnowledgeSourceType
    status: KnowledgeSourceStatus
    file_path: str | None
    website_url: str | None
    file_size_bytes: int | None
    content_type: str | None
    original_filename: str | None
    processing_stage: KnowledgeProcessingStage | None
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    processing_error: str | None
    progress_pct: int
    chunk_count: int
    embedding_count: int
    embedding_model: str | None
    embedding_status: KnowledgeEmbeddingStatus
    vector_namespace: str
    vector_store_type: VectorStoreType | None
    chunk_config: ChunkConfig | None
    metadata: dict | None = Field(default=None, validation_alias="metadata_")


class KnowledgeSourceFrontendRead(KnowledgeSourceRead):
    """Frontend-ready response with derived display fields."""

    processing_percent: int = Field(description="Alias for progress_pct")
    file_size_display: str | None = None
    embedding_status_label: str
    is_processing: bool
    created_date: datetime

    @classmethod
    def from_source(cls, source: KnowledgeSourceRead) -> "KnowledgeSourceFrontendRead":
        return cls(
            **source.model_dump(),
            processing_percent=source.progress_pct,
            file_size_display=_format_file_size(source.file_size_bytes),
            embedding_status_label=source.embedding_status.value.replace("_", " ").title(),
            is_processing=source.status
            in (KnowledgeSourceStatus.PROCESSING, KnowledgeSourceStatus.REPROCESSING),
            created_date=source.created_at,
        )


class KnowledgeSourceStatusSummary(SchemaBase):
    tenant_id: UUID
    total_sources: int
    pending: int
    processing: int
    ready: int
    failed: int
    total_chunks: int
    total_embeddings: int


class KnowledgeReprocessRequest(SchemaBase):
    source_ids: list[UUID] | None = Field(
        default=None,
        description="Specific sources to reprocess; omit to reprocess all failed sources",
    )
    chunk_config: ChunkConfig | None = None
    force: bool = Field(default=False, description="Reprocess even if status is ready")


def _format_file_size(size_bytes: int | None) -> str | None:
    if size_bytes is None:
        return None
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
