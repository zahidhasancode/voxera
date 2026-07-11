"""Background processing interface for knowledge ingestion."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.knowledge.schemas.ingestion import IngestionJobStatus, IngestionJobSubmit


class BackgroundIngestionProcessor(ABC):
    """Port for enqueueing ingestion jobs (Celery, ARQ, SQS, etc.)."""

    @abstractmethod
    async def submit(self, job: IngestionJobSubmit) -> IngestionJobStatus:
        raise NotImplementedError

    @abstractmethod
    async def get_status(self, job_id: str) -> IngestionJobStatus | None:
        raise NotImplementedError

    @abstractmethod
    async def cancel(self, job_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def submit_reprocess(
        self,
        tenant_id: UUID,
        source_id: UUID,
    ) -> IngestionJobStatus:
        raise NotImplementedError
