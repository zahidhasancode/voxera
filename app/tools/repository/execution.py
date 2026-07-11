"""Repository ports for tool execution framework."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.tools.schemas.execution import (
    TenantToolConfigRead,
    ToolAuditRead,
    ToolExecutionRead,
    ToolPermissionRead,
)


class ToolPermissionRepository(ABC):
    @abstractmethod
    async def list_for_tenant(
        self,
        tenant_id: UUID,
        *,
        agent_id: UUID | None = None,
    ) -> list[ToolPermissionRead]:
        ...

    @abstractmethod
    async def upsert(self, permission: ToolPermissionRead) -> ToolPermissionRead:
        ...


class TenantToolConfigRepository(ABC):
    @abstractmethod
    async def get(self, tenant_id: UUID, tool_slug: str) -> TenantToolConfigRead | None:
        ...

    @abstractmethod
    async def list_for_tenant(self, tenant_id: UUID) -> list[TenantToolConfigRead]:
        ...

    @abstractmethod
    async def upsert(self, config: TenantToolConfigRead) -> TenantToolConfigRead:
        ...


class ToolFrameworkExecutionRepository(ABC):
    @abstractmethod
    async def create(self, execution: ToolExecutionRead) -> ToolExecutionRead:
        ...

    @abstractmethod
    async def get_by_idempotency(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        idempotency_key: str,
    ) -> ToolExecutionRead | None:
        ...

    @abstractmethod
    async def list_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
        tool_slug: str | None = None,
        limit: int = 50,
    ) -> list[ToolExecutionRead]:
        ...

    @abstractmethod
    async def count_since(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        tool_slug: str,
        *,
        since_minutes: int = 60,
    ) -> int:
        ...

    @abstractmethod
    async def metrics_snapshot(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        tool_slug: str | None = None,
    ) -> dict:
        ...


class ToolAuditRepository(ABC):
    @abstractmethod
    async def append(self, audit: ToolAuditRead) -> ToolAuditRead:
        ...

    @abstractmethod
    async def list_for_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 100,
    ) -> list[ToolAuditRead]:
        ...
