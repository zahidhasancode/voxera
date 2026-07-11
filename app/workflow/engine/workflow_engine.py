"""WorkflowEngine port."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.workflow.schemas import (
    ApproveWorkflowRequest,
    AdvanceWorkflowRequest,
    StartWorkflowRequest,
    TestWorkflowRequest,
    ValidateWorkflowRequest,
    WorkflowExecutionRead,
    WorkflowMetricsSnapshot,
    WorkflowRead,
    WorkflowStepResult,
)


class WorkflowEngine(ABC):
    @abstractmethod
    async def start(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: StartWorkflowRequest,
    ) -> WorkflowStepResult:
        ...

    @abstractmethod
    async def advance(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: AdvanceWorkflowRequest,
    ) -> WorkflowStepResult:
        ...

    @abstractmethod
    async def approve(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: ApproveWorkflowRequest,
    ) -> WorkflowStepResult:
        ...

    @abstractmethod
    async def pause(self, tenant_id: UUID, agent_id: UUID, execution_id: UUID) -> WorkflowStepResult:
        ...

    @abstractmethod
    async def resume(self, tenant_id: UUID, agent_id: UUID, execution_id: UUID) -> WorkflowStepResult:
        ...

    @abstractmethod
    async def reject(self, tenant_id: UUID, agent_id: UUID, execution_id: UUID, *, reason: str) -> WorkflowStepResult:
        ...

    @abstractmethod
    async def test(self, tenant_id: UUID, agent_id: UUID, request: TestWorkflowRequest) -> WorkflowStepResult:
        ...

    @abstractmethod
    async def validate(self, request: ValidateWorkflowRequest) -> list[str]:
        ...

    @abstractmethod
    async def list_workflows(self, tenant_id: UUID) -> list[WorkflowRead]:
        ...

    @abstractmethod
    async def get_workflow(self, tenant_id: UUID, workflow_id: UUID) -> WorkflowRead:
        ...

    @abstractmethod
    async def get_execution(self, tenant_id: UUID, agent_id: UUID, execution_id: UUID) -> WorkflowExecutionRead:
        ...

    @abstractmethod
    async def get_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ) -> list:
        ...

    @abstractmethod
    async def get_metrics(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
    ) -> WorkflowMetricsSnapshot:
        ...
