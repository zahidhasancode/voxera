"""Audit log repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.audit.schemas import AuditLogCreate, AuditLogFilter, AuditLogRead


class AuditLogRepository(ABC):
    @abstractmethod
    async def append(self, data: AuditLogCreate) -> AuditLogRead:
        raise NotImplementedError

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        filters: AuditLogFilter | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLogRead], int]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        tenant_id: UUID,
        audit_log_id: UUID,
    ) -> AuditLogRead | None:
        raise NotImplementedError
