"""Persistent integration sync job worker."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from app.core.enums import IntegrationSyncJobStatus
from app.core.logger import get_logger
from app.database.models.integration import IntegrationSyncJobModel
from app.database.session import session_scope
from app.infrastructure.repositories.integration.repositories import SqlAlchemyIntegrationRepository
from app.integrations.monitoring.metrics import integration_metrics
from app.integrations.providers.base import ConnectionContext
from app.integrations.providers.registry import integration_provider_registry
from app.integrations.sync.engine import sync_engine

logger = get_logger(__name__)


class IntegrationSyncWorker:
    """Background worker for integration sync jobs."""

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}

    async def enqueue(self, job_id: uuid.UUID) -> None:
        if str(job_id) in self._tasks:
            return
        self._tasks[str(job_id)] = asyncio.create_task(self._run(job_id))

    async def cancel(self, job_id: uuid.UUID) -> bool:
        task = self._tasks.pop(str(job_id), None)
        if task and not task.done():
            task.cancel()
            return True
        return False

    async def _run(self, job_id: uuid.UUID) -> None:
        try:
            async with session_scope() as session:
                repo = SqlAlchemyIntegrationRepository(session)
                job = await repo.get_sync_job(job_id)
                if job is None:
                    return
                job.status = IntegrationSyncJobStatus.RUNNING.value
                job.started_at = datetime.now(timezone.utc)
                job.worker_id = str(uuid.uuid4())[:8]
                await repo.update_sync_job(job)

                connection = await repo.get_connection(job.tenant_id, job.connection_id)
                if connection is None:
                    job.status = IntegrationSyncJobStatus.FAILED.value
                    job.error = "Connection not found"
                    job.completed_at = datetime.now(timezone.utc)
                    await repo.update_sync_job(job)
                    return

                credentials_rows = await repo.get_credentials(connection.id)
                credentials = {}
                if credentials_rows:
                    from app.integrations.credentials.store import credential_store

                    credentials = credential_store.decrypt_payload(
                        credentials_rows[0].encrypted_payload
                    )

                mappings = await repo.list_field_mappings(connection.id)
                field_map: dict[str, list[dict]] = {}
                for m in mappings:
                    field_map.setdefault(m.entity_type, []).append(
                        {
                            "source_field": m.source_field,
                            "target_field": m.target_field,
                            "transform": m.transform,
                            "is_active": m.is_active,
                            "entity_type": m.entity_type,
                        }
                    )

                cursors = {
                    c.entity_type: c.cursor_value for c in await repo.list_cursors(connection.id)
                }

                ctx = ConnectionContext(
                    tenant_id=connection.tenant_id,
                    connection_id=connection.id,
                    provider_slug=connection.provider_slug,
                    config=connection.config or {},
                    credentials=credentials,
                    field_mappings=field_map,
                )

                from app.core.enums import IntegrationEntityType, IntegrationSyncMode

                entity_types = [
                    IntegrationEntityType(e) for e in (job.entity_types or [])
                ]
                result = await sync_engine.run_sync(
                    ctx=ctx,
                    entity_types=entity_types,
                    mode=IntegrationSyncMode(job.sync_mode),
                    cursors=cursors,
                )

                job.records_processed = result["records_processed"]
                job.progress_pct = 100
                job.status = IntegrationSyncJobStatus.COMPLETED.value
                job.completed_at = datetime.now(timezone.utc)
                connection.last_sync_at = job.completed_at
                connection.health_status = "healthy"
                await repo.update_sync_job(job)
                await repo.update_connection(connection)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Integration sync job failed", extra_fields={"job_id": str(job_id)})
            integration_metrics.record_sync("unknown", 0, success=False)
            async with session_scope() as session:
                repo = SqlAlchemyIntegrationRepository(session)
                job = await repo.get_sync_job(job_id)
                if job:
                    job.retry_count += 1
                    if job.retry_count >= job.max_retries:
                        job.status = IntegrationSyncJobStatus.DEAD_LETTER.value
                    else:
                        job.status = IntegrationSyncJobStatus.RETRYING.value
                    job.error = str(exc)
                    job.completed_at = datetime.now(timezone.utc)
                    await repo.update_sync_job(job)
        finally:
            self._tasks.pop(str(job_id), None)


integration_sync_worker = IntegrationSyncWorker()
