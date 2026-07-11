"""Workflow repository ports."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.workflow.schemas import WorkflowAuditRead, WorkflowCreate, WorkflowExecutionRead, WorkflowRead


class WorkflowRepository(ABC):
    @abstractmethod
    async def create(self, data: WorkflowCreate, tenant_id: UUID) -> WorkflowRead:
        ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, workflow_id: UUID) -> WorkflowRead | None:
        ...

    @abstractmethod
    async def get_by_slug(self, tenant_id: UUID, slug: str) -> WorkflowRead | None:
        ...

    @abstractmethod
    async def list_for_tenant(self, tenant_id: UUID) -> list[WorkflowRead]:
        ...


class WorkflowExecutionRepository(ABC):
    @abstractmethod
    async def create(self, execution: WorkflowExecutionRead) -> WorkflowExecutionRead:
        ...

    @abstractmethod
    async def update(self, execution: WorkflowExecutionRead) -> WorkflowExecutionRead:
        ...

    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, execution_id: UUID) -> WorkflowExecutionRead | None:
        ...

    @abstractmethod
    async def list_by_conversation(
        self, tenant_id: UUID, agent_id: UUID, conversation_id: UUID, *, limit: int = 20
    ) -> list[WorkflowExecutionRead]:
        ...

    @abstractmethod
    async def metrics_snapshot(
        self, tenant_id: UUID, agent_id: UUID, *, conversation_id: UUID | None = None
    ) -> dict:
        ...


class WorkflowRuleRepository(ABC):
    @abstractmethod
    async def list_for_tenant(self, tenant_id: UUID, *, workflow_id: UUID | None = None) -> list[dict]:
        ...


class BusinessPolicyRepository(ABC):
    @abstractmethod
    async def list_for_tenant(self, tenant_id: UUID) -> list[dict]:
        ...


class RoutingRuleRepository(ABC):
    @abstractmethod
    async def list_for_tenant(self, tenant_id: UUID) -> list[dict]:
        ...


class WorkflowAuditRepository(ABC):
    @abstractmethod
    async def append(self, entry: WorkflowAuditRead) -> WorkflowAuditRead:
        ...

    @abstractmethod
    async def list_by_conversation(
        self, tenant_id: UUID, agent_id: UUID, conversation_id: UUID, *, limit: int = 50
    ) -> list[WorkflowAuditRead]:
        ...
