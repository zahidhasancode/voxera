"""Persistent ingestion worker tests."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.knowledge.schemas.ingestion import IngestionJobSubmit


@pytest.mark.asyncio
async def test_submit_creates_job_and_schedules_task() -> None:
    from app.infrastructure.knowledge.persistent_worker import PersistentIngestionWorker

    worker = PersistentIngestionWorker()
    tenant_id = uuid4()
    source_id = uuid4()
    fake_status = MagicMock()
    fake_status.job_id = str(uuid4())
    fake_status.tenant_id = tenant_id
    fake_status.source_id = source_id

    session = AsyncMock()

    @asynccontextmanager
    async def fake_scope():
        yield session

    with patch("app.infrastructure.knowledge.persistent_worker.session_scope", fake_scope), patch(
        "app.infrastructure.knowledge.persistent_worker.KnowledgeIngestionJobRepository.create",
        new=AsyncMock(return_value=fake_status),
    ), patch.object(worker, "_run_job", new=AsyncMock()) as run_job:
        status = await worker.submit(IngestionJobSubmit(tenant_id=tenant_id, source_id=source_id))
        assert status.job_id == fake_status.job_id
        run_job.assert_not_awaited()
