"""Workflow service — thin facade over WorkflowEngine."""

from uuid import UUID

from app.workflow.engine.workflow_engine import WorkflowEngine
from app.workflow.schemas import (
    AdvanceWorkflowRequest,
    ApproveWorkflowRequest,
    StartWorkflowRequest,
    TestWorkflowRequest,
    ValidateWorkflowRequest,
    WorkflowCreate,
    WorkflowExecutionRead,
    WorkflowMetricsSnapshot,
    WorkflowRead,
    WorkflowStepResult,
)


class WorkflowService:
    def __init__(self, engine: WorkflowEngine, workflows) -> None:
        self._engine = engine
        self._workflows = workflows

    async def create_workflow(self, tenant_id: UUID, data: WorkflowCreate) -> WorkflowRead:
        violations = await self._engine.validate(ValidateWorkflowRequest(definition=data.definition))
        if violations:
            from app.core.exceptions import WorkflowValidationError
            raise WorkflowValidationError("Invalid workflow definition", violations=violations)
        return await self._workflows.create(data, tenant_id)

    async def start(self, tenant_id: UUID, agent_id: UUID, request: StartWorkflowRequest) -> WorkflowStepResult:
        return await self._engine.start(tenant_id, agent_id, request)

    async def advance(self, tenant_id: UUID, agent_id: UUID, request: AdvanceWorkflowRequest) -> WorkflowStepResult:
        return await self._engine.advance(tenant_id, agent_id, request)

    async def approve(self, tenant_id: UUID, agent_id: UUID, request: ApproveWorkflowRequest) -> WorkflowStepResult:
        return await self._engine.approve(tenant_id, agent_id, request)

    async def test(self, tenant_id: UUID, agent_id: UUID, request: TestWorkflowRequest) -> WorkflowStepResult:
        return await self._engine.test(tenant_id, agent_id, request)

    async def validate(self, request: ValidateWorkflowRequest) -> list[str]:
        return await self._engine.validate(request)

    async def list_workflows(self, tenant_id: UUID) -> list[WorkflowRead]:
        return await self._engine.list_workflows(tenant_id)

    async def get_workflow(self, tenant_id: UUID, workflow_id: UUID) -> WorkflowRead:
        return await self._engine.get_workflow(tenant_id, workflow_id)

    async def get_execution(self, tenant_id: UUID, agent_id: UUID, execution_id: UUID) -> WorkflowExecutionRead:
        return await self._engine.get_execution(tenant_id, agent_id, execution_id)

    async def get_history(self, tenant_id: UUID, agent_id: UUID, conversation_id: UUID, *, limit: int = 50) -> list:
        return await self._engine.get_history(tenant_id, agent_id, conversation_id, limit=limit)

    async def get_metrics(
        self, tenant_id: UUID, agent_id: UUID, *, conversation_id: UUID | None = None
    ) -> WorkflowMetricsSnapshot:
        return await self._engine.get_metrics(tenant_id, agent_id, conversation_id=conversation_id)

    async def reject(self, tenant_id: UUID, agent_id: UUID, execution_id: UUID, *, reason: str) -> WorkflowStepResult:
        return await self._engine.reject(tenant_id, agent_id, execution_id, reason=reason)
