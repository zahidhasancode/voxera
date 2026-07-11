"""Alembic migration — enterprise planner agent."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_enterprise_planner"
down_revision: Union[str, None] = "004_enterprise_tool_framework"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "planner_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("reasoning_step_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_intent", sa.String(length=64), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planner_sessions_tenant_id"), "planner_sessions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_planner_sessions_agent_id"), "planner_sessions", ["agent_id"], unique=False)
    op.create_index(op.f("ix_planner_sessions_conversation_id"), "planner_sessions", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_planner_sessions_status"), "planner_sessions", ["status"], unique=False)

    op.create_table(
        "planner_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("next_action", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("reasoning_steps", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("plan", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tool_call", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("policy_decisions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("token_estimate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("model_provider", sa.String(length=32), nullable=False, server_default="structured"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["planner_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planner_decisions_tenant_id"), "planner_decisions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_planner_decisions_agent_id"), "planner_decisions", ["agent_id"], unique=False)
    op.create_index(op.f("ix_planner_decisions_conversation_id"), "planner_decisions", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_planner_decisions_session_id"), "planner_decisions", ["session_id"], unique=False)
    op.create_index(op.f("ix_planner_decisions_intent"), "planner_decisions", ["intent"], unique=False)
    op.create_index(op.f("ix_planner_decisions_action"), "planner_decisions", ["action"], unique=False)
    op.create_index(op.f("ix_planner_decisions_status"), "planner_decisions", ["status"], unique=False)

    op.create_table(
        "planner_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(length=32), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("input_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decision_id"], ["planner_decisions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["planner_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planner_history_tenant_id"), "planner_history", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_planner_history_agent_id"), "planner_history", ["agent_id"], unique=False)
    op.create_index(op.f("ix_planner_history_conversation_id"), "planner_history", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_planner_history_session_id"), "planner_history", ["session_id"], unique=False)
    op.create_index(op.f("ix_planner_history_decision_id"), "planner_history", ["decision_id"], unique=False)

    op.create_table(
        "planner_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("total_plans", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("escalation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("average_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("average_reasoning_steps", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cache_hits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_misses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("calls_by_intent", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planner_metrics_tenant_id"), "planner_metrics", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_planner_metrics_agent_id"), "planner_metrics", ["agent_id"], unique=False)
    op.create_index(op.f("ix_planner_metrics_conversation_id"), "planner_metrics", ["conversation_id"], unique=False)


def downgrade() -> None:
    op.drop_table("planner_metrics")
    op.drop_table("planner_history")
    op.drop_table("planner_decisions")
    op.drop_table("planner_sessions")
