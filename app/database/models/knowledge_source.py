"""Knowledge source ORM model — uploaded document or URL for ingestion."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    KnowledgeEmbeddingStatus,
    KnowledgeProcessingStage,
    KnowledgeSourceStatus,
)
from app.database.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeSourceModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Tenant-scoped knowledge source (file upload or website URL)."""

    __tablename__ = "knowledge_sources"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=KnowledgeSourceStatus.PENDING,
        index=True,
    )

    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    processing_stage: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        default=KnowledgeProcessingStage.UPLOAD,
        index=True,
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    embedding_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=KnowledgeEmbeddingStatus.PENDING,
        index=True,
    )
    vector_namespace: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    vector_store_type: Mapped[str | None] = mapped_column(String(32), nullable=True)

    chunk_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    tenant = relationship("TenantModel", back_populates="knowledge_sources")
    chunks = relationship(
        "KnowledgeChunkModel",
        back_populates="source",
        cascade="all, delete-orphan",
    )


class KnowledgeChunkModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Persisted text chunk with metadata; vectors stored in external VectorStore."""

    __tablename__ = "knowledge_chunks"

    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vector_id: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    chunk_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    source = relationship("KnowledgeSourceModel", back_populates="chunks")
