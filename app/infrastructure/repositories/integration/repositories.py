"""SQLAlchemy integration repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.integration import (
    IntegrationAuditLogModel,
    IntegrationConnectionModel,
    IntegrationCredentialModel,
    IntegrationFieldMappingModel,
    IntegrationSyncCursorModel,
    IntegrationSyncJobModel,
    IntegrationWebhookDlqModel,
    IntegrationWebhookEventModel,
)
from app.integrations.repository.interfaces import IntegrationRepository


class SqlAlchemyIntegrationRepository(IntegrationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_connection(self, model: IntegrationConnectionModel) -> IntegrationConnectionModel:
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model

    async def get_connection_by_id(self, connection_id: UUID) -> IntegrationConnectionModel | None:
        result = await self._session.execute(
            select(IntegrationConnectionModel).where(
                IntegrationConnectionModel.id == connection_id
            )
        )
        return result.scalar_one_or_none()

    async def get_connection(
        self,
        tenant_id: UUID,
        connection_id: UUID,
    ) -> IntegrationConnectionModel | None:
        result = await self._session.execute(
            select(IntegrationConnectionModel).where(
                IntegrationConnectionModel.id == connection_id,
                IntegrationConnectionModel.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_connections(
        self,
        tenant_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[IntegrationConnectionModel], int]:
        base = select(IntegrationConnectionModel).where(
            IntegrationConnectionModel.tenant_id == tenant_id
        )
        total = await self._session.scalar(select(func.count()).select_from(base.subquery()))
        rows = await self._session.execute(base.offset(offset).limit(limit))
        return list(rows.scalars().all()), int(total or 0)

    async def update_connection(self, model: IntegrationConnectionModel) -> IntegrationConnectionModel:
        await self._session.flush()
        await self._session.refresh(model)
        return model

    async def save_credential(self, model: IntegrationCredentialModel) -> IntegrationCredentialModel:
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model

    async def get_credentials(self, connection_id: UUID) -> list[IntegrationCredentialModel]:
        rows = await self._session.execute(
            select(IntegrationCredentialModel).where(
                IntegrationCredentialModel.connection_id == connection_id
            )
        )
        return list(rows.scalars().all())

    async def save_field_mappings(
        self,
        connection_id: UUID,
        mappings: list[IntegrationFieldMappingModel],
    ) -> None:
        for mapping in mappings:
            mapping.connection_id = connection_id
            self._session.add(mapping)
        await self._session.flush()

    async def list_field_mappings(self, connection_id: UUID) -> list[IntegrationFieldMappingModel]:
        rows = await self._session.execute(
            select(IntegrationFieldMappingModel).where(
                IntegrationFieldMappingModel.connection_id == connection_id
            )
        )
        return list(rows.scalars().all())

    async def create_sync_job(self, model: IntegrationSyncJobModel) -> IntegrationSyncJobModel:
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model

    async def update_sync_job(self, model: IntegrationSyncJobModel) -> IntegrationSyncJobModel:
        await self._session.flush()
        await self._session.refresh(model)
        return model

    async def get_sync_job(self, job_id: UUID) -> IntegrationSyncJobModel | None:
        result = await self._session.execute(
            select(IntegrationSyncJobModel).where(IntegrationSyncJobModel.id == job_id)
        )
        return result.scalar_one_or_none()

    async def upsert_cursor(self, model: IntegrationSyncCursorModel) -> None:
        self._session.add(model)
        await self._session.flush()

    async def list_cursors(self, connection_id: UUID) -> list[IntegrationSyncCursorModel]:
        rows = await self._session.execute(
            select(IntegrationSyncCursorModel).where(
                IntegrationSyncCursorModel.connection_id == connection_id
            )
        )
        return list(rows.scalars().all())

    async def record_webhook_event(self, model: IntegrationWebhookEventModel) -> bool:
        existing = await self._session.execute(
            select(IntegrationWebhookEventModel).where(
                IntegrationWebhookEventModel.connection_id == model.connection_id,
                IntegrationWebhookEventModel.event_id == model.event_id,
            )
        )
        if existing.scalar_one_or_none():
            return False
        self._session.add(model)
        await self._session.flush()
        return True

    async def add_dlq(self, model: IntegrationWebhookDlqModel) -> None:
        self._session.add(model)
        await self._session.flush()

    async def append_audit(self, model: IntegrationAuditLogModel) -> IntegrationAuditLogModel:
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model

    async def list_audit(
        self,
        tenant_id: UUID,
        *,
        connection_id: UUID | None,
        offset: int,
        limit: int,
    ) -> tuple[list[IntegrationAuditLogModel], int]:
        base = select(IntegrationAuditLogModel).where(
            IntegrationAuditLogModel.tenant_id == tenant_id
        )
        if connection_id:
            base = base.where(IntegrationAuditLogModel.connection_id == connection_id)
        base = base.order_by(IntegrationAuditLogModel.created_at.desc())
        total = await self._session.scalar(select(func.count()).select_from(base.subquery()))
        rows = await self._session.execute(base.offset(offset).limit(limit))
        return list(rows.scalars().all()), int(total or 0)

    async def count_connections_by_health(self, tenant_id: UUID) -> dict[str, int]:
        rows = await self._session.execute(
            select(
                IntegrationConnectionModel.health_status,
                func.count(),
            )
            .where(IntegrationConnectionModel.tenant_id == tenant_id)
            .group_by(IntegrationConnectionModel.health_status)
        )
        return {status: count for status, count in rows.all()}

    async def count_running_jobs(self, tenant_id: UUID) -> int:
        count = await self._session.scalar(
            select(func.count())
            .select_from(IntegrationSyncJobModel)
            .where(
                IntegrationSyncJobModel.tenant_id == tenant_id,
                IntegrationSyncJobModel.status.in_(("queued", "running", "retrying")),
            )
        )
        return int(count or 0)
