"""Alembic migration — enterprise tool execution framework."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_enterprise_tool_framework"
down_revision: Union[str, None] = "003_enterprise_memory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tool_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tool_slug", sa.String(length=128), nullable=False),
        sa.Column("effect", sa.String(length=16), nullable=False, server_default="allow"),
        sa.Column("department", sa.String(length=128), nullable=True),
        sa.Column("role", sa.String(length=128), nullable=True),
        sa.Column("max_executions_per_hour", sa.Integer(), nullable=True),
        sa.Column("working_hours_start", sa.String(length=8), nullable=True),
        sa.Column("working_hours_end", sa.String(length=8), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "tool_slug", "agent_id", name="uq_tool_permissions_scope"),
    )
    op.create_index(op.f("ix_tool_permissions_tenant_id"), "tool_permissions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_tool_permissions_tool_slug"), "tool_permissions", ["tool_slug"], unique=False)
    op.create_index(op.f("ix_tool_permissions_agent_id"), "tool_permissions", ["agent_id"], unique=False)

    op.create_table(
        "tenant_tool_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_slug", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("credentials_ref", sa.String(length=512), nullable=True),
        sa.Column("provider_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=True),
        sa.Column("timeout_seconds", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "tool_slug", name="uq_tenant_tool_configs_slug"),
    )
    op.create_index(op.f("ix_tenant_tool_configs_tenant_id"), "tenant_tool_configs", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_tenant_tool_configs_tool_slug"), "tenant_tool_configs", ["tool_slug"], unique=False)

    op.create_table(
        "tool_framework_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tool_slug", sa.String(length=128), nullable=False),
        sa.Column("tool_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="success"),
        sa.Column("arguments", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tool_framework_executions_tenant_id"), "tool_framework_executions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_tool_framework_executions_agent_id"), "tool_framework_executions", ["agent_id"], unique=False)
    op.create_index(op.f("ix_tool_framework_executions_conversation_id"), "tool_framework_executions", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_tool_framework_executions_tool_slug"), "tool_framework_executions", ["tool_slug"], unique=False)
    op.create_index(op.f("ix_tool_framework_executions_status"), "tool_framework_executions", ["status"], unique=False)
    op.create_index(op.f("ix_tool_framework_executions_idempotency_key"), "tool_framework_executions", ["idempotency_key"], unique=False)

    op.create_table(
        "tool_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tool_slug", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("planner_request", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("validated_arguments", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("execution_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("execution_duration_ms", sa.Float(), nullable=True),
        sa.Column("operator", sa.String(length=128), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["execution_id"], ["tool_framework_executions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tool_audit_logs_tenant_id"), "tool_audit_logs", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_tool_audit_logs_agent_id"), "tool_audit_logs", ["agent_id"], unique=False)
    op.create_index(op.f("ix_tool_audit_logs_conversation_id"), "tool_audit_logs", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_tool_audit_logs_tool_slug"), "tool_audit_logs", ["tool_slug"], unique=False)
    op.create_index(op.f("ix_tool_audit_logs_status"), "tool_audit_logs", ["status"], unique=False)
    op.create_index(op.f("ix_tool_audit_logs_execution_id"), "tool_audit_logs", ["execution_id"], unique=False)


def downgrade() -> None:
    op.drop_table("tool_audit_logs")
    op.drop_table("tool_framework_executions")
    op.drop_table("tenant_tool_configs")
    op.drop_table("tool_permissions")
