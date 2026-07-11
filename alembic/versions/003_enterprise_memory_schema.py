"""Alembic migration — enterprise memory system."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_enterprise_memory"
down_revision: Union[str, None] = "002_knowledge_ingestion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("current_state", sa.String(length=32), nullable=False, server_default="call_started"),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("turn_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversations_agent_id"), "conversations", ["agent_id"], unique=False)
    op.create_index(op.f("ix_conversations_status"), "conversations", ["status"], unique=False)
    op.create_index(op.f("ix_conversations_current_state"), "conversations", ["current_state"], unique=False)
    op.create_index(op.f("ix_conversations_tenant_id"), "conversations", ["tenant_id"], unique=False)

    op.create_table(
        "conversation_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("tool_calls", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reasoning_steps", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversation_turns_conversation_id"), "conversation_turns", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_conversation_turns_role"), "conversation_turns", ["role"], unique=False)
    op.create_index(op.f("ix_conversation_turns_tenant_id"), "conversation_turns", ["tenant_id"], unique=False)

    op.create_table(
        "conversation_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_identity", sa.Text(), nullable=True),
        sa.Column("conversation_goal", sa.Text(), nullable=True),
        sa.Column("resolved_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("pending_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("collected_information", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("turn_count_at_summary", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversation_summaries_conversation_id"), "conversation_summaries", ["conversation_id"], unique=False)

    op.create_table(
        "working_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("memory_key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("value_type", sa.String(length=32), nullable=False, server_default="string"),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", "memory_key", name="uq_working_memory_conversation_key"),
    )
    op.create_index(op.f("ix_working_memory_conversation_id"), "working_memory", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_working_memory_memory_key"), "working_memory", ["memory_key"], unique=False)

    op.create_table(
        "tool_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("arguments", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="success"),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tool_executions_conversation_id"), "tool_executions", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_tool_executions_tool_name"), "tool_executions", ["tool_name"], unique=False)
    op.create_index(op.f("ix_tool_executions_status"), "tool_executions", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tool_executions_status"), table_name="tool_executions")
    op.drop_index(op.f("ix_tool_executions_tool_name"), table_name="tool_executions")
    op.drop_index(op.f("ix_tool_executions_conversation_id"), table_name="tool_executions")
    op.drop_table("tool_executions")

    op.drop_index(op.f("ix_working_memory_memory_key"), table_name="working_memory")
    op.drop_index(op.f("ix_working_memory_conversation_id"), table_name="working_memory")
    op.drop_table("working_memory")

    op.drop_index(op.f("ix_conversation_summaries_conversation_id"), table_name="conversation_summaries")
    op.drop_table("conversation_summaries")

    op.drop_index(op.f("ix_conversation_turns_tenant_id"), table_name="conversation_turns")
    op.drop_index(op.f("ix_conversation_turns_role"), table_name="conversation_turns")
    op.drop_index(op.f("ix_conversation_turns_conversation_id"), table_name="conversation_turns")
    op.drop_table("conversation_turns")

    op.drop_index(op.f("ix_conversations_tenant_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_current_state"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_status"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_agent_id"), table_name="conversations")
    op.drop_table("conversations")
