"""Persistent background ingestion worker with DB-backed job lifecycle."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from uuid import UUID

from app.core.config import settings
from app.core.enums import KnowledgeIngestionJobStatus, KnowledgeProcessingStage
from app.core.logger import get_logger
from app.database.session import session_scope
from app.infrastructure.knowledge.factory import build_knowledge_ingestion_service
from app.infrastructure.repositories.knowledge_job_repository import KnowledgeIngestionJobRepository
from app.knowledge.ingestion.background import BackgroundIngestionProcessor
from app.knowledge.schemas.ingestion import IngestionJobStatus, IngestionJobSubmit

logger = get_logger(__name__)


class PersistentIngestionWorker(BackgroundIngestionProcessor):
    """DB-backed ingestion worker — each job uses an isolated database session."""

    def __init__(self) -> None:
        self._worker_id = str(uuid.uuid4())
        self._tasks: dict[str, asyncio.Task] = {}

    async def submit(self, job: IngestionJobSubmit) -> IngestionJobStatus:
        async with session_scope() as session:
            repo = KnowledgeIngestionJobRepository(session)
            status = await repo.create(tenant_id=job.tenant_id, source_id=job.source_id)

        task = asyncio.create_task(self._run_job(UUID(status.job_id), job), name=f"ingestion-{status.job_id}")
        self._tasks[status.job_id] = task
        logger.info(
            "Ingestion job queued",
            extra_fields={
                "job_id": status.job_id,
                "tenant_id": str(job.tenant_id),
                "source_id": str(job.source_id),
                "worker_id": self._worker_id,
                "event": "knowledge_ingestion_job_queued",
            },
        )
        return status

    async def _run_job(self, job_id: UUID, job: IngestionJobSubmit) -> None:
        async with session_scope() as session:
            repo = KnowledgeIngestionJobRepository(session)
            await repo.mark_running(job_id, worker_id=self._worker_id)

        attempt = 0
        while attempt <= settings.KNOWLEDGE_JOB_MAX_RETRIES:
            try:
                async with session_scope() as session:
                    ingestion = build_knowledge_ingestion_service(session)
                    await ingestion.run_processing(job.tenant_id, job.source_id)
                async with session_scope() as session:
                    repo = KnowledgeIngestionJobRepository(session)
                    await repo.mark_completed(job_id)
                logger.info(
                    "Ingestion job completed",
                    extra_fields={"job_id": str(job_id), "worker_id": self._worker_id},
                )
                return
            except asyncio.CancelledError:
                async with session_scope() as session:
                    repo = KnowledgeIngestionJobRepository(session)
                    await repo.mark_cancelled(job_id)
                raise
            except Exception as exc:
                attempt += 1
                retrying = attempt <= settings.KNOWLEDGE_JOB_MAX_RETRIES
                async with session_scope() as session:
                    repo = KnowledgeIngestionJobRepository(session)
                    await repo.mark_failed(job_id, error=str(exc), retrying=retrying)
                if not retrying:
                    logger.error(
                        "Ingestion job failed",
                        extra_fields={
                            "job_id": str(job_id),
                            "error": str(exc),
                            "attempts": attempt,
                        },
                    )
                    return
                logger.warning(
                    "Ingestion job retry",
                    extra_fields={"job_id": str(job_id), "attempt": attempt},
                )
                await asyncio.sleep(settings.KNOWLEDGE_JOB_RETRY_DELAY_SECONDS)

    async def get_status(self, job_id: str) -> IngestionJobStatus | None:
        async with session_scope() as session:
            repo = KnowledgeIngestionJobRepository(session)
            return await repo.get(UUID(job_id))

    async def cancel(self, job_id: str) -> bool:
        task = self._tasks.get(job_id)
        if task is None or task.done():
            async with session_scope() as session:
                repo = KnowledgeIngestionJobRepository(session)
                await repo.mark_cancelled(UUID(job_id))
            return False
        task.cancel()
        return True

    async def submit_reprocess(self, tenant_id: UUID, source_id: UUID) -> IngestionJobStatus:
        return await self.submit(IngestionJobSubmit(source_id=source_id, tenant_id=tenant_id))


persistent_ingestion_worker = PersistentIngestionWorker()
