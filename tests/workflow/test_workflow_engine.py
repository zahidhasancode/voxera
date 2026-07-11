"""WorkflowEngine integration tests with in-memory repositories."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.core.enums import WorkflowExecutionStatus, WorkflowState
from app.infrastructure.workflow.workflow_engine_impl import WorkflowEngineImpl
from app.workflow.audit.audit_service import WorkflowAuditService
from app.workflow.schemas import (
    ApproveWorkflowRequest,
    StartWorkflowRequest,
    TestWorkflowRequest,
    ValidateWorkflowRequest,
    WorkflowCreate,
    WorkflowExecutionRead,
    WorkflowRead,
)


class InMemoryWorkflowRepo:
    def __init__(self) -> None:
        self._items: dict[UUID, WorkflowRead] = {}

    async def create(self, data: WorkflowCreate, tenant_id: UUID) -> WorkflowRead:
        now = datetime.now(timezone.utc)
        wf = WorkflowRead(
            id=uuid4(),
            tenant_id=tenant_id,
            slug=data.slug,
            name=data.name,
            description=data.description,
            version=data.version,
            enabled=data.enabled,
            definition=data.definition,
            created_at=now,
            updated_at=now,
        )
        self._items[wf.id] = wf
        return wf

    async def get_by_id(self, tenant_id: UUID, workflow_id: UUID) -> WorkflowRead | None:
        wf = self._items.get(workflow_id)
        return wf if wf and wf.tenant_id == tenant_id else None

    async def get_by_slug(self, tenant_id: UUID, slug: str) -> WorkflowRead | None:
        for wf in self._items.values():
            if wf.tenant_id == tenant_id and wf.slug == slug:
                return wf
        return None

    async def list_for_tenant(self, tenant_id: UUID) -> list[WorkflowRead]:
        return [w for w in self._items.values() if w.tenant_id == tenant_id]


class InMemoryExecutionRepo:
    def __init__(self) -> None:
        self._items: dict[UUID, WorkflowExecutionRead] = {}

    async def create(self, execution: WorkflowExecutionRead) -> WorkflowExecutionRead:
        self._items[execution.id] = execution
        return execution

    async def update(self, execution: WorkflowExecutionRead) -> WorkflowExecutionRead:
        self._items[execution.id] = execution
        return execution

    async def get_by_id(self, tenant_id: UUID, execution_id: UUID) -> WorkflowExecutionRead | None:
        ex = self._items.get(execution_id)
        return ex if ex and ex.tenant_id == tenant_id else None

    async def metrics_snapshot(self, tenant_id: UUID, agent_id: UUID, *, conversation_id: UUID | None = None) -> dict:
        rows = [e for e in self._items.values() if e.tenant_id == tenant_id and e.agent_id == agent_id]
        return {
            "total_executions": len(rows),
            "completed_count": sum(1 for r in rows if r.status == WorkflowExecutionStatus.COMPLETED),
            "failed_count": sum(1 for r in rows if r.status == WorkflowExecutionStatus.FAILED),
            "escalated_count": sum(1 for r in rows if r.status == WorkflowExecutionStatus.ESCALATED),
        }


class InMemoryAuditRepo:
    def __init__(self) -> None:
        self.entries = []

    async def append(self, entry):
        self.entries.append(entry)
        return entry

    async def list_by_conversation(self, tenant_id, agent_id, conversation_id, *, limit=50):
        return [e for e in self.entries if e.conversation_id == conversation_id][:limit]


class EmptyRepo:
    async def list_for_tenant(self, *args, **kwargs):
        return []


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def agent_id():
    return uuid4()


@pytest.fixture
async def engine(tenant_id):
    workflows = InMemoryWorkflowRepo()
    now = datetime.now(timezone.utc)
    wf_id = uuid4()
    workflows._items[wf_id] = WorkflowRead(
        id=wf_id,
        tenant_id=tenant_id,
        slug="default",
        name="Default",
        description=None,
        version="1.0.0",
        enabled=True,
        definition={
            "slug": "default",
            "rules": [
                {
                    "name": "high_refund",
                    "priority": 10,
                    "enabled": True,
                    "conditions": [{"field": "refund_amount", "operator": "gt", "value": 500}],
                    "actions": [{"type": "require_approval", "params": {"role": "manager"}}],
                }
            ],
            "approval_chain": [{"role": "supervisor"}, {"role": "finance"}],
        },
        created_at=now,
        updated_at=now,
    )
    audit_repo = InMemoryAuditRepo()
    return WorkflowEngineImpl(
        workflows=workflows,
        executions=InMemoryExecutionRepo(),
        rules_repo=EmptyRepo(),
        policies_repo=EmptyRepo(),
        routing_repo=EmptyRepo(),
        audit=WorkflowAuditService(audit_repo),
    ), workflows, audit_repo


@pytest.mark.asyncio
async def test_start_workflow_requires_approval(engine, tenant_id, agent_id):
    eng, _, _ = engine
    result = await eng.start(
        tenant_id,
        agent_id,
        StartWorkflowRequest(
            conversation_id=uuid4(),
            workflow_slug="default",
            context={"refund_amount": 750},
        ),
    )
    assert result.state == WorkflowState.WAITING_APPROVAL
    assert result.requires_approval


@pytest.mark.asyncio
async def test_test_workflow_reject_rule(engine, tenant_id, agent_id):
    eng, _, _ = engine
    result = await eng.test(
        tenant_id,
        agent_id,
        TestWorkflowRequest(
            definition={
                "rules": [
                    {
                        "name": "reject_large",
                        "priority": 1,
                        "enabled": True,
                        "conditions": [{"field": "amount", "operator": "gt", "value": 10000}],
                        "actions": [{"type": "reject", "params": {"reason": "Amount too large"}}],
                    }
                ]
            },
            context={"amount": 50000},
        ),
    )
    assert result.state == WorkflowState.REJECTED
    assert result.completed


@pytest.mark.asyncio
async def test_validate_definition(engine):
    eng, _, _ = engine
    violations = await eng.validate(ValidateWorkflowRequest(definition={"name": "Test", "slug": "test"}))
    assert violations == []


@pytest.mark.asyncio
async def test_approve_workflow_two_step(engine, tenant_id, agent_id):
    eng, _, audit_repo = engine
    conversation_id = uuid4()
    start = await eng.start(
        tenant_id,
        agent_id,
        StartWorkflowRequest(
            conversation_id=conversation_id,
            workflow_slug="default",
            context={"refund_amount": 750},
        ),
    )
    assert start.approval_id is not None
    execution_id = next(iter(eng._executions._items.keys()))

    first = await eng.approve(
        tenant_id,
        agent_id,
        ApproveWorkflowRequest(
            execution_id=execution_id,
            approval_id=start.approval_id,
            approved=True,
        ),
    )
    assert first.state == WorkflowState.WAITING_APPROVAL

    pending = eng._executions._items[execution_id].context["pending_approvals"]
    second_id = next(a["id"] for a in pending if a["status"] == "pending")
    final = await eng.approve(
        tenant_id,
        agent_id,
        ApproveWorkflowRequest(
            execution_id=execution_id,
            approval_id=second_id,
            approved=True,
        ),
    )
    assert final.state == WorkflowState.EXECUTING
    assert len(audit_repo.entries) >= 2
