"""Audit log application service interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.audit.schemas import AuditLogCreate, AuditLogFilter, AuditLogRead


class AuditLogService(ABC):
    @abstractmethod
    async def record_event(self, data: AuditLogCreate) -> AuditLogRead:
        raise NotImplementedError

    @abstractmethod
    async def list_events(
        self,
        tenant_id: UUID,
        *,
        filters: AuditLogFilter | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLogRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def get_event(self, tenant_id: UUID, audit_log_id: UUID) -> AuditLogRead:
        raise NotImplementedError
