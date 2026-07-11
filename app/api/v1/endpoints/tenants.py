"""Tenant REST endpoints — no business logic; delegates to TenantService."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_tenant_service, map_domain_errors
from app.core.schemas import PaginatedResponse
from app.tenants.schemas import TenantCreate, TenantRead, TenantUpdate
from app.tenants.service import TenantService

router = APIRouter()


class TenantListResponse(PaginatedResponse):
    items: list[TenantRead]


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreate,
    service: TenantService = Depends(get_tenant_service),
) -> TenantRead:
    return await service.create_tenant(body)


@router.get("", response_model=TenantListResponse)
async def list_tenants(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: TenantService = Depends(get_tenant_service),
) -> TenantListResponse:
    items, total = await service.list_tenants(offset=offset, limit=limit)
    return TenantListResponse(total=total, offset=offset, limit=limit, items=items)


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(
    tenant_id: UUID,
    service: TenantService = Depends(get_tenant_service),
) -> TenantRead:
    try:
        return await service.get_tenant(tenant_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.patch("/{tenant_id}", response_model=TenantRead)
async def update_tenant(
    tenant_id: UUID,
    body: TenantUpdate,
    service: TenantService = Depends(get_tenant_service),
) -> TenantRead:
    try:
        return await service.update_tenant(tenant_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID,
    service: TenantService = Depends(get_tenant_service),
) -> None:
    try:
        await service.delete_tenant(tenant_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc
