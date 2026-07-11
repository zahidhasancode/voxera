"""Integration service port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.integrations.schemas.connection import (
    IntegrationAuditLogRead,
    IntegrationConnectRequest,
    IntegrationConnectResponse,
    IntegrationConnectionRead,
    IntegrationDisconnectRequest,
    IntegrationMetricsSnapshot,
    IntegrationStatusResponse,
    IntegrationSyncJobRead,
    IntegrationSyncRequest,
    PaginatedIntegrationConnections,
    PaginatedIntegrationLogs,
    ProviderCatalogEntry,
)


class IntegrationService(ABC):
    @abstractmethod
    async def list_catalog(self) -> list[ProviderCatalogEntry]: ...

    @abstractmethod
    async def list_connections(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> PaginatedIntegrationConnections: ...

    @abstractmethod
    async def connect(
        self,
        tenant_id: UUID,
        request: IntegrationConnectRequest,
    ) -> IntegrationConnectResponse: ...

    @abstractmethod
    async def disconnect(
        self,
        tenant_id: UUID,
        request: IntegrationDisconnectRequest,
    ) -> IntegrationConnectionRead: ...

    @abstractmethod
    async def get_status(
        self,
        tenant_id: UUID,
        connection_id: UUID,
    ) -> IntegrationStatusResponse: ...

    @abstractmethod
    async def trigger_sync(
        self,
        tenant_id: UUID,
        request: IntegrationSyncRequest,
    ) -> IntegrationSyncJobRead: ...

    @abstractmethod
    async def list_logs(
        self,
        tenant_id: UUID,
        *,
        connection_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> PaginatedIntegrationLogs: ...

    @abstractmethod
    async def get_metrics(self, tenant_id: UUID) -> IntegrationMetricsSnapshot: ...

    @abstractmethod
    async def handle_oauth_callback(
        self,
        *,
        state: str,
        code: str,
    ) -> IntegrationConnectionRead: ...

    @abstractmethod
    async def handle_webhook(
        self,
        *,
        connection_id: UUID,
        payload: dict,
        headers: dict[str, str],
    ) -> dict: ...
