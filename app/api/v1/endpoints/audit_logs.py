"""Audit log REST endpoints (append-only)."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_audit_log_service, map_domain_errors
from app.audit.schemas import AuditLogCreate, AuditLogFilter, AuditLogRead
from app.audit.service import AuditLogService
from app.core.enums import AuditActorType
from app.core.schemas import PaginatedResponse

router = APIRouter()


class AuditLogListResponse(PaginatedResponse):
    items: list[AuditLogRead]


@router.post("", response_model=AuditLogRead, status_code=status.HTTP_201_CREATED)
async def record_audit_event(
    tenant_id: UUID,
    body: AuditLogCreate,
    service: AuditLogService = Depends(get_audit_log_service),
) -> AuditLogRead:
    payload = body.model_copy(update={"tenant_id": tenant_id})
    return await service.record_event(payload)


@router.get("", response_model=AuditLogListResponse)
async def list_audit_events(
    tenant_id: UUID,
    action: str | None = None,
    actor_type: AuditActorType | None = None,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: AuditLogService = Depends(get_audit_log_service),
) -> AuditLogListResponse:
    filters = AuditLogFilter(
        action=action,
        actor_type=actor_type,
        resource_type=resource_type,
        resource_id=resource_id,
        since=since,
        until=until,
    )
    items, total = await service.list_events(
        tenant_id,
        filters=filters,
        offset=offset,
        limit=limit,
    )
    return AuditLogListResponse(total=total, offset=offset, limit=limit, items=items)


@router.get("/{audit_log_id}", response_model=AuditLogRead)
async def get_audit_event(
    tenant_id: UUID,
    audit_log_id: UUID,
    service: AuditLogService = Depends(get_audit_log_service),
) -> AuditLogRead:
    try:
        return await service.get_event(tenant_id, audit_log_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc
