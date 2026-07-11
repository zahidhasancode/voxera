"""Audit log service implementation."""

from uuid import UUID

from app.audit.schemas import AuditLogCreate, AuditLogFilter, AuditLogRead
from app.audit.service import AuditLogService
from app.core.exceptions import NotFoundError
from app.infrastructure.repositories.audit_repository import SqlAlchemyAuditLogRepository


class AuditLogServiceImpl(AuditLogService):
    def __init__(self, repository: SqlAlchemyAuditLogRepository) -> None:
        self._repository = repository

    async def record_event(self, data: AuditLogCreate) -> AuditLogRead:
        return await self._repository.append(data)

    async def list_events(
        self,
        tenant_id: UUID,
        *,
        filters: AuditLogFilter | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLogRead], int]:
        return await self._repository.list_by_tenant(
            tenant_id,
            filters=filters,
            offset=offset,
            limit=limit,
        )

    async def get_event(self, tenant_id: UUID, audit_log_id: UUID) -> AuditLogRead:
        row = await self._repository.get_by_id(tenant_id, audit_log_id)
        if row is None:
            raise NotFoundError(f"Audit log {audit_log_id} not found")
        return row
