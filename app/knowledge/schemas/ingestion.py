"""Ingestion pipeline Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.core.enums import KnowledgeIngestionJobStatus, KnowledgeProcessingStage
from app.core.schemas import SchemaBase


class IngestionJobSubmit(SchemaBase):
    source_id: UUID
    tenant_id: UUID


class IngestionJobStatus(SchemaBase):
    job_id: str
    source_id: UUID
    tenant_id: UUID
    status: KnowledgeIngestionJobStatus = KnowledgeIngestionJobStatus.QUEUED
    stage: KnowledgeProcessingStage = KnowledgeProcessingStage.UPLOAD
    progress_pct: int = 0
    retry_count: int = 0
    worker_id: str | None = None
    submitted_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


class ProcessingMetricsSnapshot(SchemaBase):
    tenant_id: UUID
    source_id: UUID
    processing_time_ms: int | None = None
    chunk_count: int = 0
    embedding_count: int = 0
    average_chunk_size_chars: float | None = None
    average_chunk_tokens: float | None = None
    documents_processed: int = 1
    stage_durations_ms: dict[str, int] = Field(default_factory=dict)
