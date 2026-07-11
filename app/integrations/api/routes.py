"""Integration platform REST API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_integration_service, map_domain_errors
from app.integrations.schemas.connection import (
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

router = APIRouter()


@router.get("/catalog", response_model=list[ProviderCatalogEntry])
async def list_provider_catalog(
    service: IntegrationService = Depends(get_integration_service),
) -> list[ProviderCatalogEntry]:
    return await service.list_catalog()


@router.get("", response_model=PaginatedIntegrationConnections)
async def list_integrations(
    tenant_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: IntegrationService = Depends(get_integration_service),
) -> PaginatedIntegrationConnections:
    return await service.list_connections(tenant_id, offset=offset, limit=limit)


@router.post("/connect", response_model=IntegrationConnectResponse, status_code=status.HTTP_201_CREATED)
async def connect_integration(
    tenant_id: UUID,
    body: IntegrationConnectRequest,
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationConnectResponse:
    try:
        return await service.connect(tenant_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.post("/disconnect", response_model=IntegrationConnectionRead)
async def disconnect_integration(
    tenant_id: UUID,
    body: IntegrationDisconnectRequest,
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationConnectionRead:
    try:
        return await service.disconnect(tenant_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/status/{connection_id}", response_model=IntegrationStatusResponse)
async def integration_status(
    tenant_id: UUID,
    connection_id: UUID,
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationStatusResponse:
    try:
        return await service.get_status(tenant_id, connection_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/logs", response_model=PaginatedIntegrationLogs)
async def integration_logs(
    tenant_id: UUID,
    connection_id: UUID | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: IntegrationService = Depends(get_integration_service),
) -> PaginatedIntegrationLogs:
    return await service.list_logs(
        tenant_id,
        connection_id=connection_id,
        offset=offset,
        limit=limit,
    )


@router.post("/sync", response_model=IntegrationSyncJobRead, status_code=status.HTTP_202_ACCEPTED)
async def trigger_sync(
    tenant_id: UUID,
    body: IntegrationSyncRequest,
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationSyncJobRead:
    try:
        return await service.trigger_sync(tenant_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/metrics", response_model=IntegrationMetricsSnapshot)
async def integration_metrics(
    tenant_id: UUID,
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationMetricsSnapshot:
    return await service.get_metrics(tenant_id)
