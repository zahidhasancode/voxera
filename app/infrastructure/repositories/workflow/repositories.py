"""SQLAlchemy workflow repositories."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.workflow import (
    BusinessPolicyModel,
    RoutingRuleModel,
    WorkflowAuditModel,
    WorkflowExecutionModel,
    WorkflowModel,
    WorkflowRuleModel,
)
from app.workflow.repository import (
    BusinessPolicyRepository,
    RoutingRuleRepository,
    WorkflowAuditRepository,
    WorkflowExecutionRepository,
    WorkflowRepository,
    WorkflowRuleRepository,
)
from app.workflow.schemas import WorkflowAuditRead, WorkflowCreate, WorkflowExecutionRead, WorkflowRead


class SqlAlchemyWorkflowRepository(WorkflowRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: WorkflowCreate, tenant_id: UUID) -> WorkflowRead:
        row = WorkflowModel(
            tenant_id=tenant_id,
            slug=data.slug,
            name=data.name,
            description=data.description,
            version=data.version,
            enabled=data.enabled,
            definition=data.definition,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return WorkflowRead.model_validate(row)

    async def get_by_id(self, tenant_id: UUID, workflow_id: UUID) -> WorkflowRead | None:
        result = await self._session.execute(
            select(WorkflowModel).where(WorkflowModel.tenant_id == tenant_id, WorkflowModel.id == workflow_id)
        )
        row = result.scalar_one_or_none()
        return WorkflowRead.model_validate(row) if row else None

    async def get_by_slug(self, tenant_id: UUID, slug: str) -> WorkflowRead | None:
        result = await self._session.execute(
            select(WorkflowModel).where(WorkflowModel.tenant_id == tenant_id, WorkflowModel.slug == slug)
        )
        row = result.scalar_one_or_none()
        return WorkflowRead.model_validate(row) if row else None

    async def list_for_tenant(self, tenant_id: UUID) -> list[WorkflowRead]:
        result = await self._session.execute(
            select(WorkflowModel).where(WorkflowModel.tenant_id == tenant_id, WorkflowModel.enabled.is_(True))
        )
        return [WorkflowRead.model_validate(r) for r in result.scalars().all()]


class SqlAlchemyWorkflowExecutionRepository(WorkflowExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, execution: WorkflowExecutionRead) -> WorkflowExecutionRead:
        row = WorkflowExecutionModel(
            id=execution.id,
            tenant_id=execution.tenant_id,
            agent_id=execution.agent_id,
            workflow_id=execution.workflow_id,
            conversation_id=execution.conversation_id,
            status=execution.status.value,
            current_state=execution.current_state.value,
            context=execution.context,
            step_index=execution.step_index,
            retry_count=execution.retry_count,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            expires_at=execution.expires_at,
            error=execution.error,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return WorkflowExecutionRead.model_validate(row)

    async def update(self, execution: WorkflowExecutionRead) -> WorkflowExecutionRead:
        result = await self._session.execute(
            select(WorkflowExecutionModel).where(WorkflowExecutionModel.id == execution.id)
        )
        row = result.scalar_one()
        row.status = execution.status.value
        row.current_state = execution.current_state.value
        row.context = execution.context
        row.step_index = execution.step_index
        row.retry_count = execution.retry_count
        row.completed_at = execution.completed_at
        row.error = execution.error
        await self._session.flush()
        await self._session.refresh(row)
        return WorkflowExecutionRead.model_validate(row)

    async def get_by_id(self, tenant_id: UUID, execution_id: UUID) -> WorkflowExecutionRead | None:
        result = await self._session.execute(
            select(WorkflowExecutionModel).where(
                WorkflowExecutionModel.tenant_id == tenant_id,
                WorkflowExecutionModel.id == execution_id,
            )
        )
        row = result.scalar_one_or_none()
        return WorkflowExecutionRead.model_validate(row) if row else None

    async def list_by_conversation(
        self, tenant_id: UUID, agent_id: UUID, conversation_id: UUID, *, limit: int = 20
    ) -> list[WorkflowExecutionRead]:
        result = await self._session.execute(
            select(WorkflowExecutionModel)
            .where(
                WorkflowExecutionModel.tenant_id == tenant_id,
                WorkflowExecutionModel.agent_id == agent_id,
                WorkflowExecutionModel.conversation_id == conversation_id,
            )
            .order_by(WorkflowExecutionModel.created_at.desc())
            .limit(limit)
        )
        return [WorkflowExecutionRead.model_validate(r) for r in result.scalars().all()]

    async def metrics_snapshot(
        self, tenant_id: UUID, agent_id: UUID, *, conversation_id: UUID | None = None
    ) -> dict:
        query = select(WorkflowExecutionModel).where(
            WorkflowExecutionModel.tenant_id == tenant_id,
            WorkflowExecutionModel.agent_id == agent_id,
        )
        if conversation_id:
            query = query.where(WorkflowExecutionModel.conversation_id == conversation_id)
        result = await self._session.execute(query)
        rows = list(result.scalars().all())
        if not rows:
            return {}
        return {
            "total_executions": len(rows),
            "completed_count": sum(1 for r in rows if r.status == "completed"),
            "failed_count": sum(1 for r in rows if r.status == "failed"),
            "escalated_count": sum(1 for r in rows if r.status == "escalated"),
        }


class SqlAlchemyWorkflowRuleRepository(WorkflowRuleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_tenant(self, tenant_id: UUID, *, workflow_id: UUID | None = None) -> list[dict]:
        query = select(WorkflowRuleModel).where(
            WorkflowRuleModel.tenant_id == tenant_id, WorkflowRuleModel.enabled.is_(True)
        )
        if workflow_id:
            query = query.where(
                (WorkflowRuleModel.workflow_id == workflow_id) | (WorkflowRuleModel.workflow_id.is_(None))
            )
        result = await self._session.execute(query.order_by(WorkflowRuleModel.priority))
        return [
            {
                "name": r.name,
                "priority": r.priority,
                "enabled": r.enabled,
                "conditions": r.conditions,
                "actions": r.actions,
                "else_actions": r.else_actions or [],
            }
            for r in result.scalars().all()
        ]


class SqlAlchemyBusinessPolicyRepository(BusinessPolicyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_tenant(self, tenant_id: UUID) -> list[dict]:
        result = await self._session.execute(
            select(BusinessPolicyModel).where(
                BusinessPolicyModel.tenant_id == tenant_id, BusinessPolicyModel.enabled.is_(True)
            )
        )
        return [
            {"policy_key": r.policy_key, "policy_value": r.policy_value, "enabled": r.enabled, "department": r.department}
            for r in result.scalars().all()
        ]


class SqlAlchemyRoutingRuleRepository(RoutingRuleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_tenant(self, tenant_id: UUID) -> list[dict]:
        result = await self._session.execute(
            select(RoutingRuleModel).where(
                RoutingRuleModel.tenant_id == tenant_id, RoutingRuleModel.enabled.is_(True)
            ).order_by(RoutingRuleModel.priority)
        )
        return [
            {
                "name": r.name,
                "strategy": r.strategy,
                "priority": r.priority,
                "enabled": r.enabled,
                "conditions": r.conditions,
                "target": r.target,
            }
            for r in result.scalars().all()
        ]


class SqlAlchemyWorkflowAuditRepository(WorkflowAuditRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, entry: WorkflowAuditRead) -> WorkflowAuditRead:
        row = WorkflowAuditModel(
            id=entry.id,
            tenant_id=entry.tenant_id,
            agent_id=entry.agent_id,
            execution_id=entry.execution_id,
            conversation_id=entry.conversation_id,
            event_type=entry.event_type,
            payload=entry.payload,
            operator=entry.operator,
            occurred_at=entry.occurred_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return WorkflowAuditRead.model_validate(row)

    async def list_by_conversation(
        self, tenant_id: UUID, agent_id: UUID, conversation_id: UUID, *, limit: int = 50
    ) -> list[WorkflowAuditRead]:
        result = await self._session.execute(
            select(WorkflowAuditModel)
            .where(
                WorkflowAuditModel.tenant_id == tenant_id,
                WorkflowAuditModel.agent_id == agent_id,
                WorkflowAuditModel.conversation_id == conversation_id,
            )
            .order_by(WorkflowAuditModel.occurred_at.desc())
            .limit(limit)
        )
        return [WorkflowAuditRead.model_validate(r) for r in result.scalars().all()]
