"""Integration service implementation."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from app.core.enums import (
    IntegrationAuthType,
    IntegrationCategory,
    IntegrationConnectionStatus,
    IntegrationCredentialType,
    IntegrationEntityType,
    IntegrationHealthStatus,
    IntegrationSyncJobStatus,
    IntegrationSyncMode,
    IntegrationWebhookEventStatus,
)
from app.core.exceptions import NotFoundError
from app.database.models.integration import (
    IntegrationAuditLogModel,
    IntegrationConnectionModel,
    IntegrationCredentialModel,
    IntegrationFieldMappingModel,
    IntegrationSyncJobModel,
    IntegrationWebhookEventModel,
)
from app.infrastructure.integrations.sync_worker import integration_sync_worker
from app.infrastructure.repositories.integration.repositories import SqlAlchemyIntegrationRepository
from app.integrations.credentials.store import credential_store
from app.integrations.monitoring.metrics import integration_metrics
from app.integrations.oauth.manager import integration_oauth_manager
from app.integrations.providers.base import ConnectionContext
from app.integrations.providers.registry import integration_provider_registry
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
from app.integrations.services.integration_service import IntegrationService
from app.integrations.webhooks.processor import webhook_processor


class IntegrationServiceImpl(IntegrationService):
    def __init__(self, repository: SqlAlchemyIntegrationRepository) -> None:
        self._repo = repository

    async def list_catalog(self) -> list[ProviderCatalogEntry]:
        return [
            ProviderCatalogEntry(
                slug=p.metadata.slug.value,
                name=p.metadata.name,
                category=p.metadata.category,
                auth_type=p.metadata.auth_type,
                description=p.metadata.description,
                supported_entities=list(p.metadata.supported_entities),
                docs_url=p.metadata.docs_url,
            )
            for p in integration_provider_registry.list_providers()
        ]

    async def list_connections(
        self,
        tenant_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> PaginatedIntegrationConnections:
        rows, total = await self._repo.list_connections(tenant_id, offset=offset, limit=limit)
        items = [self._to_connection_read(r) for r in rows]
        return PaginatedIntegrationConnections(items=items, total=total, offset=offset, limit=limit)

    async def connect(
        self,
        tenant_id: uuid.UUID,
        request: IntegrationConnectRequest,
    ) -> IntegrationConnectResponse:
        provider = integration_provider_registry.get(request.provider_slug)
        meta = provider.metadata

        connection = IntegrationConnectionModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            provider_slug=meta.slug.value,
            category=meta.category.value,
            auth_type=meta.auth_type.value,
            status=IntegrationConnectionStatus.PENDING.value,
            display_name=request.display_name,
            config=request.config,
            oauth_scopes=list(meta.default_scopes),
            health_status=IntegrationHealthStatus.UNKNOWN.value,
        )
        webhook_secret = secrets.token_urlsafe(32)
        connection.webhook_secret_hash = hashlib.sha256(webhook_secret.encode()).hexdigest()
        connection = await self._repo.create_connection(connection)

        if request.credentials:
            cred_type = (
                IntegrationCredentialType.OAUTH2.value
                if meta.auth_type == IntegrationAuthType.OAUTH2
                else IntegrationCredentialType.API_KEY.value
            )
            await self._repo.save_credential(
                IntegrationCredentialModel(
                    id=uuid.uuid4(),
                    connection_id=connection.id,
                    credential_type=cred_type,
                    encrypted_payload=credential_store.encrypt_payload(request.credentials),
                )
            )

        if request.field_mappings:
            mappings = [
                IntegrationFieldMappingModel(
                    id=uuid.uuid4(),
                    connection_id=connection.id,
                    entity_type=m.entity_type.value,
                    source_field=m.source_field,
                    target_field=m.target_field,
                    transform=m.transform,
                    is_active=m.is_active,
                )
                for m in request.field_mappings
            ]
            await self._repo.save_field_mappings(connection.id, mappings)

        ctx = await self._build_context(connection)
        connect_result = await provider.connect(ctx, redirect_uri=request.redirect_uri)

        connection.status = connect_result.status.value
        if connect_result.status == IntegrationConnectionStatus.CONNECTED:
            connection.health_status = IntegrationHealthStatus.HEALTHY.value
        connection = await self._repo.update_connection(connection)

        await self._repo.append_audit(
            IntegrationAuditLogModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                connection_id=connection.id,
                action="connect",
                detail={"provider": request.provider_slug, "status": connection.status},
            )
        )

        webhook_url = f"/api/v1/integrations/webhooks/{connection.id}"
        return IntegrationConnectResponse(
            connection=self._to_connection_read(connection, meta.supported_entities),
            authorization_url=connect_result.authorization_url,
            webhook_url=webhook_url,
        )

    async def disconnect(
        self,
        tenant_id: uuid.UUID,
        request: IntegrationDisconnectRequest,
    ) -> IntegrationConnectionRead:
        connection = await self._require_connection(tenant_id, request.connection_id)
        provider = integration_provider_registry.get(connection.provider_slug)
        ctx = await self._build_context(connection)
        await provider.disconnect(ctx)

        connection.status = IntegrationConnectionStatus.DISCONNECTED.value
        connection.health_status = IntegrationHealthStatus.UNKNOWN.value
        connection = await self._repo.update_connection(connection)

        await self._repo.append_audit(
            IntegrationAuditLogModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                connection_id=connection.id,
                action="disconnect",
                detail={},
            )
        )
        return self._to_connection_read(connection)

    async def get_status(
        self,
        tenant_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> IntegrationStatusResponse:
        connection = await self._require_connection(tenant_id, connection_id)
        provider = integration_provider_registry.get(connection.provider_slug)
        ctx = await self._build_context(connection)
        started = datetime.now(timezone.utc)
        health = await provider.health(ctx)
        latency_ms = health.latency_ms or (
            (datetime.now(timezone.utc) - started).total_seconds() * 1000
        )

        connection.health_status = health.status.value
        connection.last_health_at = datetime.now(timezone.utc)
        connection.error_message = health.message
        await self._repo.update_connection(connection)

        return IntegrationStatusResponse(
            connection_id=connection.id,
            provider_slug=connection.provider_slug,
            status=IntegrationConnectionStatus(connection.status),
            health_status=health.status,
            last_sync_at=connection.last_sync_at,
            latency_ms=round(latency_ms, 2),
            message=health.message,
        )

    async def trigger_sync(
        self,
        tenant_id: uuid.UUID,
        request: IntegrationSyncRequest,
    ) -> IntegrationSyncJobRead:
        connection = await self._require_connection(tenant_id, request.connection_id)
        entity_values = [e.value for e in request.entity_types] if request.entity_types else []

        job = IntegrationSyncJobModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            connection_id=connection.id,
            sync_mode=request.sync_mode.value,
            entity_types=entity_values,
            status=IntegrationSyncJobStatus.QUEUED.value,
        )
        job = await self._repo.create_sync_job(job)
        await integration_sync_worker.enqueue(job.id)

        await self._repo.append_audit(
            IntegrationAuditLogModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                connection_id=connection.id,
                action="sync_triggered",
                detail={"job_id": str(job.id), "mode": request.sync_mode.value},
            )
        )
        return self._to_job_read(job)

    async def list_logs(
        self,
        tenant_id: uuid.UUID,
        *,
        connection_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> PaginatedIntegrationLogs:
        rows, total = await self._repo.list_audit(
            tenant_id,
            connection_id=connection_id,
            offset=offset,
            limit=limit,
        )
        items = [
            IntegrationAuditLogRead(
                id=r.id,
                tenant_id=r.tenant_id,
                connection_id=r.connection_id,
                action=r.action,
                detail=r.detail,
                created_at=r.created_at,
            )
            for r in rows
        ]
        return PaginatedIntegrationLogs(items=items, total=total, offset=offset, limit=limit)

    async def get_metrics(self, tenant_id: uuid.UUID) -> IntegrationMetricsSnapshot:
        health_counts = await self._repo.count_connections_by_health(tenant_id)
        platform = integration_metrics.snapshot()
        _, total = await self._repo.list_connections(tenant_id, offset=0, limit=1)
        return IntegrationMetricsSnapshot(
            total_connections=total,
            healthy_connections=health_counts.get("healthy", 0),
            degraded_connections=health_counts.get("degraded", 0),
            failed_connections=health_counts.get("unhealthy", 0),
            sync_jobs_running=await self._repo.count_running_jobs(tenant_id),
            avg_sync_latency_ms=platform["avg_sync_latency_ms"],
            avg_webhook_latency_ms=platform["avg_webhook_latency_ms"],
            oauth_refresh_count_24h=platform["oauth_refresh_count"],
        )

    async def handle_oauth_callback(self, *, state: str, code: str) -> IntegrationConnectionRead:
        try:
            tenant_str, conn_str = state.split(":", 1)
            tenant_id = uuid.UUID(tenant_str)
            connection_id = uuid.UUID(conn_str)
        except ValueError as exc:
            raise ValueError("Invalid OAuth state") from exc

        connection = await self._require_connection(tenant_id, connection_id)
        provider = integration_provider_registry.get(connection.provider_slug)
        meta = provider.metadata
        if not meta.oauth_token_url:
            raise ValueError("Provider does not support OAuth token exchange")

        token_data = await integration_oauth_manager.exchange_code(
            token_url=meta.oauth_token_url,
            code=code,
            redirect_uri=connection.config.get("redirect_uri", ""),
            client_id=connection.config.get("client_id", ""),
            client_secret=connection.config.get("client_secret", ""),
        )
        integration_metrics.record_oauth_refresh()

        expires_at = integration_oauth_manager.compute_expiry(token_data)
        await self._repo.save_credential(
            IntegrationCredentialModel(
                id=uuid.uuid4(),
                connection_id=connection.id,
                credential_type=IntegrationCredentialType.OAUTH2.value,
                encrypted_payload=credential_store.encrypt_payload(token_data),
                expires_at=expires_at,
            )
        )

        connection.status = IntegrationConnectionStatus.CONNECTED.value
        connection.health_status = IntegrationHealthStatus.HEALTHY.value
        connection = await self._repo.update_connection(connection)
        return self._to_connection_read(connection)

    async def handle_webhook(
        self,
        *,
        connection_id: uuid.UUID,
        payload: dict,
        headers: dict[str, str],
    ) -> dict:
        connection = await self._repo.get_connection_by_id(connection_id)
        if connection is None:
            raise NotFoundError(f"Connection {connection_id} not found")

        ctx = await self._build_context(connection)
        event_id = str(payload.get("id") or payload.get("event_id") or uuid.uuid4())

        recorded = await self._repo.record_webhook_event(
            IntegrationWebhookEventModel(
                id=uuid.uuid4(),
                connection_id=connection.id,
                event_id=event_id,
                provider_event_type=str(payload.get("type") or payload.get("event") or ""),
                payload_hash=hashlib.sha256(str(payload).encode()).hexdigest(),
                status=IntegrationWebhookEventStatus.RECEIVED.value,
            )
        )
        if not recorded:
            return {"status": IntegrationWebhookEventStatus.DUPLICATE.value, "event_id": event_id}

        try:
            return await webhook_processor.ingest(
                ctx=ctx,
                payload=payload,
                headers=headers,
                event_id=event_id,
            )
        except Exception as exc:
            from app.database.models.integration import IntegrationWebhookDlqModel

            await self._repo.add_dlq(
                IntegrationWebhookDlqModel(
                    id=uuid.uuid4(),
                    connection_id=connection.id,
                    event_id=event_id,
                    payload=payload,
                    error=str(exc),
                )
            )
            raise

    async def _require_connection(
        self,
        tenant_id: uuid.UUID,
        connection_id: uuid.UUID,
    ) -> IntegrationConnectionModel:
        connection = await self._repo.get_connection(tenant_id, connection_id)
        if connection is None:
            raise NotFoundError(f"Integration connection {connection_id} not found")
        return connection

    async def _build_context(self, connection: IntegrationConnectionModel) -> ConnectionContext:
        cred_rows = await self._repo.get_credentials(connection.id)
        credentials = {}
        if cred_rows:
            credentials = credential_store.decrypt_payload(cred_rows[-1].encrypted_payload)

        mappings = await self._repo.list_field_mappings(connection.id)
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

        return ConnectionContext(
            tenant_id=connection.tenant_id,
            connection_id=connection.id,
            provider_slug=connection.provider_slug,
            config=connection.config or {},
            credentials=credentials,
            field_mappings=field_map,
        )

    def _to_connection_read(
        self,
        model: IntegrationConnectionModel,
        supported: tuple | None = None,
    ) -> IntegrationConnectionRead:
        entities: list[IntegrationEntityType] = []
        if supported:
            entities = list(supported)
        else:
            try:
                provider = integration_provider_registry.get(model.provider_slug)
                entities = list(provider.metadata.supported_entities)
            except KeyError:
                pass

        return IntegrationConnectionRead(
            id=model.id,
            tenant_id=model.tenant_id,
            provider_slug=model.provider_slug,
            category=IntegrationCategory(model.category),
            auth_type=IntegrationAuthType(model.auth_type),
            status=IntegrationConnectionStatus(model.status),
            display_name=model.display_name,
            health_status=IntegrationHealthStatus(model.health_status),
            last_sync_at=model.last_sync_at,
            last_health_at=model.last_health_at,
            error_message=model.error_message,
            sync_schedule_cron=model.sync_schedule_cron,
            supported_entities=entities,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_job_read(job: IntegrationSyncJobModel) -> IntegrationSyncJobRead:
        return IntegrationSyncJobRead(
            id=job.id,
            tenant_id=job.tenant_id,
            connection_id=job.connection_id,
            sync_mode=IntegrationSyncMode(job.sync_mode),
            entity_types=job.entity_types or [],
            status=IntegrationSyncJobStatus(job.status),
            progress_pct=job.progress_pct,
            records_processed=job.records_processed,
            records_failed=job.records_failed,
            error=job.error,
            submitted_at=job.submitted_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
