"""Integration platform Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.core.enums import (
    IntegrationAuthType,
    IntegrationCategory,
    IntegrationConnectionStatus,
    IntegrationEntityType,
    IntegrationHealthStatus,
    IntegrationSyncJobStatus,
    IntegrationSyncMode,
)
from app.core.schemas import SchemaBase


class ProviderCatalogEntry(SchemaBase):
    slug: str
    name: str
    category: IntegrationCategory
    auth_type: IntegrationAuthType
    description: str
    supported_entities: list[IntegrationEntityType]
    docs_url: str | None = None


class FieldMappingCreate(SchemaBase):
    entity_type: IntegrationEntityType
    source_field: str
    target_field: str
    transform: dict[str, Any] | None = None
    is_active: bool = True


class IntegrationConnectRequest(SchemaBase):
    provider_slug: str
    display_name: str
    config: dict[str, Any] = Field(default_factory=dict)
    credentials: dict[str, Any] = Field(default_factory=dict)
    redirect_uri: str | None = None
    entity_types: list[IntegrationEntityType] = Field(default_factory=list)
    field_mappings: list[FieldMappingCreate] = Field(default_factory=list)


class IntegrationDisconnectRequest(SchemaBase):
    connection_id: UUID


class IntegrationSyncRequest(SchemaBase):
    connection_id: UUID
    sync_mode: IntegrationSyncMode = IntegrationSyncMode.INCREMENTAL
    entity_types: list[IntegrationEntityType] = Field(default_factory=list)


class FieldMappingRead(FieldMappingCreate):
    id: UUID
    connection_id: UUID


class IntegrationConnectionRead(SchemaBase):
    id: UUID
    tenant_id: UUID
    provider_slug: str
    category: IntegrationCategory
    auth_type: IntegrationAuthType
    status: IntegrationConnectionStatus
    display_name: str
    health_status: IntegrationHealthStatus
    last_sync_at: datetime | None = None
    last_health_at: datetime | None = None
    error_message: str | None = None
    sync_schedule_cron: str | None = None
    supported_entities: list[IntegrationEntityType] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class IntegrationConnectResponse(SchemaBase):
    connection: IntegrationConnectionRead
    authorization_url: str | None = None
    webhook_url: str | None = None


class IntegrationStatusResponse(SchemaBase):
    connection_id: UUID
    provider_slug: str
    status: IntegrationConnectionStatus
    health_status: IntegrationHealthStatus
    last_sync_at: datetime | None = None
    latency_ms: float | None = None
    message: str | None = None


class IntegrationSyncJobRead(SchemaBase):
    id: UUID
    tenant_id: UUID
    connection_id: UUID
    sync_mode: IntegrationSyncMode
    entity_types: list[str]
    status: IntegrationSyncJobStatus
    progress_pct: int
    records_processed: int
    records_failed: int
    error: str | None = None
    submitted_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class IntegrationAuditLogRead(SchemaBase):
    id: UUID
    tenant_id: UUID
    connection_id: UUID | None = None
    action: str
    detail: dict[str, Any] | None = None
    created_at: datetime


class IntegrationMetricsSnapshot(SchemaBase):
    total_connections: int = 0
    healthy_connections: int = 0
    degraded_connections: int = 0
    failed_connections: int = 0
    sync_jobs_running: int = 0
    sync_jobs_failed_24h: int = 0
    webhook_events_24h: int = 0
    avg_sync_latency_ms: float = 0.0
    avg_webhook_latency_ms: float = 0.0
    oauth_refresh_count_24h: int = 0


class PaginatedIntegrationConnections(SchemaBase):
    items: list[IntegrationConnectionRead]
    total: int
    offset: int
    limit: int


class PaginatedIntegrationLogs(SchemaBase):
    items: list[IntegrationAuditLogRead]
    total: int
    offset: int
    limit: int
