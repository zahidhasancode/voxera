"""Enterprise workflow engine ORM models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import WorkflowApprovalStatus, WorkflowExecutionStatus, WorkflowState
from app.database.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Tenant workflow definition / template."""

    __tablename__ = "workflows"
    __table_args__ = (UniqueConstraint("tenant_id", "slug", name="uq_workflows_tenant_slug"),)

    slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    definition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class WorkflowExecutionModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Running or completed workflow instance."""

    __tablename__ = "workflow_executions"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workflow_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=WorkflowExecutionStatus.RUNNING, index=True
    )
    current_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default=WorkflowState.STARTED, index=True
    )
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class WorkflowRuleModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Configurable IF/THEN business rule."""

    __tablename__ = "workflow_rules"

    workflow_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    conditions: Mapped[list] = mapped_column(JSONB, nullable=False)
    actions: Mapped[list] = mapped_column(JSONB, nullable=False)
    else_actions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class WorkflowApprovalModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Approval request within a workflow execution."""

    __tablename__ = "workflow_approvals"

    execution_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    approval_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=WorkflowApprovalStatus.PENDING, index=True
    )
    approver_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approver_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class WorkflowEscalationModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Escalation record."""

    __tablename__ = "workflow_escalations"

    execution_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    context_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class BusinessPolicyModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Tenant business policy configuration."""

    __tablename__ = "business_policies"
    __table_args__ = (UniqueConstraint("tenant_id", "policy_key", name="uq_business_policies_key"),)

    policy_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    policy_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class RoutingRuleModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Tenant routing rule."""

    __tablename__ = "routing_rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    strategy: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    conditions: Mapped[list] = mapped_column(JSONB, nullable=False)
    target: Mapped[dict] = mapped_column(JSONB, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class WorkflowAuditModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Immutable workflow audit log."""

    __tablename__ = "workflow_audit_logs"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    conversation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    operator: Mapped[str | None] = mapped_column(String(128), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
