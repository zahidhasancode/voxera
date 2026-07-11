"""In-process async background processor for knowledge ingestion."""

import asyncio
import uuid
from datetime import datetime, timezone
from uuid import UUID

from app.core.enums import KnowledgeProcessingStage
from app.core.logger import get_logger
from app.knowledge.ingestion.background import BackgroundIngestionProcessor
from app.knowledge.schemas.ingestion import IngestionJobStatus, IngestionJobSubmit
from app.knowledge.services.ingestion_service import KnowledgeIngestionService

logger = get_logger(__name__)


class AsyncInProcessIngestionProcessor(BackgroundIngestionProcessor):
    """
    Enqueues ingestion jobs as asyncio tasks.

    Replace with Celery/ARQ/SQS worker in production for horizontal scale.
    """

    def __init__(self, ingestion_service: KnowledgeIngestionService) -> None:
        self._ingestion = ingestion_service
        self._jobs: dict[str, IngestionJobStatus] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    async def submit(self, job: IngestionJobSubmit) -> IngestionJobStatus:
        job_id = str(uuid.uuid4())
        status = IngestionJobStatus(
            job_id=job_id,
            source_id=job.source_id,
            tenant_id=job.tenant_id,
            stage=KnowledgeProcessingStage.UPLOAD,
            progress_pct=0,
            submitted_at=datetime.now(timezone.utc),
        )
        self._jobs[job_id] = status

        async def _run() -> None:
            started = datetime.now(timezone.utc)
            self._jobs[job_id] = status.model_copy(update={"started_at": started})
            try:
                await self._ingestion.run_processing(job.tenant_id, job.source_id)
                self._jobs[job_id] = status.model_copy(
                    update={
                        "stage": KnowledgeProcessingStage.COMPLETE,
                        "progress_pct": 100,
                        "completed_at": datetime.now(timezone.utc),
                    }
                )
            except Exception as exc:
                self._jobs[job_id] = status.model_copy(
                    update={
                        "stage": KnowledgeProcessingStage.FAILED,
                        "error": str(exc),
                        "completed_at": datetime.now(timezone.utc),
                    }
                )

        task = asyncio.create_task(_run(), name=f"ingestion-{job_id}")
        self._tasks[job_id] = task
        logger.info(
            "Ingestion job submitted",
            extra_fields={
                "job_id": job_id,
                "tenant_id": str(job.tenant_id),
                "source_id": str(job.source_id),
                "event": "knowledge_ingestion_job_submitted",
            },
        )
        return status

    async def get_status(self, job_id: str) -> IngestionJobStatus | None:
        return self._jobs.get(job_id)

    async def cancel(self, job_id: str) -> bool:
        task = self._tasks.get(job_id)
        if task is None or task.done():
            return False
        task.cancel()
        return True

    async def submit_reprocess(self, tenant_id: UUID, source_id: UUID) -> IngestionJobStatus:
        return await self.submit(IngestionJobSubmit(source_id=source_id, tenant_id=tenant_id))
