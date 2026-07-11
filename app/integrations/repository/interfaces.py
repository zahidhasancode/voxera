"""Integration repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

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


class IntegrationRepository(ABC):
    @abstractmethod
    async def create_connection(self, model: IntegrationConnectionModel) -> IntegrationConnectionModel: ...

    @abstractmethod
    async def get_connection_by_id(self, connection_id: UUID) -> IntegrationConnectionModel | None: ...

    @abstractmethod
    async def get_connection(
        self,
        tenant_id: UUID,
        connection_id: UUID,
    ) -> IntegrationConnectionModel | None: ...

    @abstractmethod
    async def list_connections(
        self,
        tenant_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[IntegrationConnectionModel], int]: ...

    @abstractmethod
    async def update_connection(self, model: IntegrationConnectionModel) -> IntegrationConnectionModel: ...

    @abstractmethod
    async def save_credential(self, model: IntegrationCredentialModel) -> IntegrationCredentialModel: ...

    @abstractmethod
    async def get_credentials(self, connection_id: UUID) -> list[IntegrationCredentialModel]: ...

    @abstractmethod
    async def save_field_mappings(
        self,
        connection_id: UUID,
        mappings: list[IntegrationFieldMappingModel],
    ) -> None: ...

    @abstractmethod
    async def list_field_mappings(self, connection_id: UUID) -> list[IntegrationFieldMappingModel]: ...

    @abstractmethod
    async def create_sync_job(self, model: IntegrationSyncJobModel) -> IntegrationSyncJobModel: ...

    @abstractmethod
    async def update_sync_job(self, model: IntegrationSyncJobModel) -> IntegrationSyncJobModel: ...

    @abstractmethod
    async def get_sync_job(self, job_id: UUID) -> IntegrationSyncJobModel | None: ...

    @abstractmethod
    async def upsert_cursor(self, model: IntegrationSyncCursorModel) -> None: ...

    @abstractmethod
    async def list_cursors(self, connection_id: UUID) -> list[IntegrationSyncCursorModel]: ...

    @abstractmethod
    async def record_webhook_event(self, model: IntegrationWebhookEventModel) -> bool: ...

    @abstractmethod
    async def add_dlq(self, model: IntegrationWebhookDlqModel) -> None: ...

    @abstractmethod
    async def append_audit(self, model: IntegrationAuditLogModel) -> IntegrationAuditLogModel: ...

    @abstractmethod
    async def list_audit(
        self,
        tenant_id: UUID,
        *,
        connection_id: UUID | None,
        offset: int,
        limit: int,
    ) -> tuple[list[IntegrationAuditLogModel], int]: ...

    @abstractmethod
    async def count_connections_by_health(
        self,
        tenant_id: UUID,
    ) -> dict[str, int]: ...

    @abstractmethod
    async def count_running_jobs(self, tenant_id: UUID) -> int: ...
