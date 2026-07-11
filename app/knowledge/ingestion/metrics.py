"""Processing metrics collector for knowledge ingestion."""

import time
from contextlib import contextmanager
from typing import Generator

from app.core.logger import get_logger
from app.knowledge.schemas.ingestion import ProcessingMetricsSnapshot

logger = get_logger(__name__)


class ProcessingMetricsCollector:
    """Collects per-source ingestion metrics and emits structured logs."""

    def __init__(self, tenant_id, source_id) -> None:
        from uuid import UUID

        self.tenant_id: UUID = tenant_id
        self.source_id: UUID = source_id
        self._started_at = time.monotonic()
        self._stage_started: dict[str, float] = {}
        self._stage_durations_ms: dict[str, int] = {}
        self.chunk_count = 0
        self.embedding_count = 0
        self._chunk_char_total = 0
        self._chunk_token_total = 0

    @contextmanager
    def stage(self, stage_name: str) -> Generator[None, None, None]:
        self._stage_started[stage_name] = time.monotonic()
        logger.info(
            f"{stage_name} started",
            extra_fields={
                "tenant_id": str(self.tenant_id),
                "source_id": str(self.source_id),
                "stage": stage_name,
                "event": "knowledge_processing_stage_started",
            },
        )
        try:
            yield
            duration_ms = int((time.monotonic() - self._stage_started[stage_name]) * 1000)
            self._stage_durations_ms[stage_name] = duration_ms
            logger.info(
                f"{stage_name} completed",
                extra_fields={
                    "tenant_id": str(self.tenant_id),
                    "source_id": str(self.source_id),
                    "stage": stage_name,
                    "duration_ms": duration_ms,
                    "event": "knowledge_processing_stage_completed",
                },
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - self._stage_started.get(stage_name, time.monotonic())) * 1000)
            logger.error(
                f"{stage_name} failed",
                extra_fields={
                    "tenant_id": str(self.tenant_id),
                    "source_id": str(self.source_id),
                    "stage": stage_name,
                    "duration_ms": duration_ms,
                    "error": str(exc),
                    "event": "knowledge_processing_stage_failed",
                },
            )
            raise

    def record_chunks(self, chunks: list) -> None:
        self.chunk_count = len(chunks)
        for chunk in chunks:
            self._chunk_char_total += getattr(chunk, "char_count", len(getattr(chunk, "content", "")))
            tokens = getattr(chunk, "token_count", None)
            if tokens:
                self._chunk_token_total += tokens

    def record_embeddings(self, count: int) -> None:
        self.embedding_count = count
        logger.info(
            "Embedding started",
            extra_fields={
                "tenant_id": str(self.tenant_id),
                "source_id": str(self.source_id),
                "embedding_count": count,
                "event": "knowledge_embedding_started",
            },
        )

    def snapshot(self) -> ProcessingMetricsSnapshot:
        elapsed_ms = int((time.monotonic() - self._started_at) * 1000)
        avg_chars = self._chunk_char_total / self.chunk_count if self.chunk_count else None
        avg_tokens = self._chunk_token_total / self.chunk_count if self.chunk_count and self._chunk_token_total else None
        snapshot = ProcessingMetricsSnapshot(
            tenant_id=self.tenant_id,
            source_id=self.source_id,
            processing_time_ms=elapsed_ms,
            chunk_count=self.chunk_count,
            embedding_count=self.embedding_count,
            average_chunk_size_chars=avg_chars,
            average_chunk_tokens=avg_tokens,
            documents_processed=1,
            stage_durations_ms=self._stage_durations_ms,
        )
        logger.info(
            "Knowledge processing completed",
            extra_fields={
                **snapshot.model_dump(mode="json"),
                "event": "knowledge_processing_completed",
            },
        )
        return snapshot
