"""Knowledge ingestion job repository."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import KnowledgeIngestionJobStatus, KnowledgeProcessingStage
from app.core.config import settings
from app.database.models.knowledge_job import KnowledgeIngestionJobModel
from app.knowledge.schemas.ingestion import IngestionJobStatus


class KnowledgeIngestionJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, tenant_id: UUID, source_id: UUID) -> IngestionJobStatus:
        job_id = uuid4()
        now = datetime.now(timezone.utc)
        row = KnowledgeIngestionJobModel(
            id=job_id,
            tenant_id=tenant_id,
            source_id=source_id,
            status=KnowledgeIngestionJobStatus.QUEUED.value,
            stage=KnowledgeProcessingStage.UPLOAD.value,
            progress_pct=0,
            retry_count=0,
            max_retries=settings.KNOWLEDGE_JOB_MAX_RETRIES,
            submitted_at=now,
        )
        self._session.add(row)
        await self._session.flush()
        return self._to_schema(row)

    async def get(self, job_id: UUID) -> IngestionJobStatus | None:
        row = await self._session.get(KnowledgeIngestionJobModel, job_id)
        return self._to_schema(row) if row else None

    async def mark_running(self, job_id: UUID, *, worker_id: str) -> None:
        row = await self._session.get(KnowledgeIngestionJobModel, job_id)
        if row:
            row.status = KnowledgeIngestionJobStatus.RUNNING.value
            row.worker_id = worker_id
            row.started_at = datetime.now(timezone.utc)
            await self._session.flush()

    async def mark_completed(self, job_id: UUID) -> None:
        row = await self._session.get(KnowledgeIngestionJobModel, job_id)
        if row:
            row.status = KnowledgeIngestionJobStatus.COMPLETED.value
            row.stage = KnowledgeProcessingStage.COMPLETE.value
            row.progress_pct = 100
            row.completed_at = datetime.now(timezone.utc)
            row.error = None
            await self._session.flush()

    async def mark_failed(self, job_id: UUID, *, error: str, retrying: bool = False) -> None:
        row = await self._session.get(KnowledgeIngestionJobModel, job_id)
        if row:
            row.status = (
                KnowledgeIngestionJobStatus.RETRYING.value
                if retrying
                else KnowledgeIngestionJobStatus.FAILED.value
            )
            row.stage = KnowledgeProcessingStage.FAILED.value
            row.error = error
            row.completed_at = datetime.now(timezone.utc) if not retrying else None
            if retrying:
                row.retry_count += 1
            await self._session.flush()

    async def mark_cancelled(self, job_id: UUID) -> None:
        row = await self._session.get(KnowledgeIngestionJobModel, job_id)
        if row:
            row.status = KnowledgeIngestionJobStatus.CANCELLED.value
            row.completed_at = datetime.now(timezone.utc)
            await self._session.flush()

    async def list_for_source(self, tenant_id: UUID, source_id: UUID) -> list[IngestionJobStatus]:
        result = await self._session.execute(
            select(KnowledgeIngestionJobModel)
            .where(
                KnowledgeIngestionJobModel.tenant_id == tenant_id,
                KnowledgeIngestionJobModel.source_id == source_id,
            )
            .order_by(KnowledgeIngestionJobModel.submitted_at.desc())
        )
        return [self._to_schema(r) for r in result.scalars().all()]

    def _to_schema(self, row: KnowledgeIngestionJobModel) -> IngestionJobStatus:
        return IngestionJobStatus(
            job_id=str(row.id),
            source_id=row.source_id,
            tenant_id=row.tenant_id,
            status=KnowledgeIngestionJobStatus(row.status),
            stage=KnowledgeProcessingStage(row.stage) if row.stage else KnowledgeProcessingStage.UPLOAD,
            progress_pct=row.progress_pct,
            retry_count=row.retry_count,
            worker_id=row.worker_id,
            submitted_at=row.submitted_at,
            started_at=row.started_at,
            completed_at=row.completed_at,
            error=row.error,
        )
