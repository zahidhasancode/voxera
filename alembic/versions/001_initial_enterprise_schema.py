"""Initial enterprise multi-tenant schema.

Revision ID: 001_initial_enterprise
Revises:
Create Date: 2026-07-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_enterprise"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("contact_email", sa.String(length=320), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("languages", postgresql.ARRAY(sa.String(length=16)), server_default="{}", nullable=False),
        sa.Column("subscription_plan", sa.String(length=32), nullable=False, server_default="free"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_tenants_slug"), "tenants", ["slug"], unique=False)
    op.create_index(op.f("ix_tenants_status"), "tenants", ["status"], unique=False)

    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("voice", sa.String(length=64), nullable=False, server_default="default"),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="en-US"),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("max_reasoning_steps", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("planner_model", sa.String(length=128), nullable=False, server_default="default"),
        sa.Column("verifier_model", sa.String(length=128), nullable=False, server_default="default"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agents_status"), "agents", ["status"], unique=False)
    op.create_index(op.f("ix_agents_tenant_id"), "agents", ["tenant_id"], unique=False)

    op.create_table(
        "agent_configurations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("identity_verification_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("escalation_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("fallback_message", sa.Text(), nullable=True),
        sa.Column("allowed_tool_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("working_hours", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_tone", sa.String(length=64), nullable=True),
        sa.Column("max_conversation_length", sa.Integer(), nullable=True),
        sa.Column("extra_settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", name="uq_agent_configurations_agent_id"),
    )
    op.create_index(op.f("ix_agent_configurations_agent_id"), "agent_configurations", ["agent_id"], unique=False)
    op.create_index(op.f("ix_agent_configurations_tenant_id"), "agent_configurations", ["tenant_id"], unique=False)

    op.create_table(
        "knowledge_bases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="processing"),
        sa.Column("embedding_model", sa.String(length=128), nullable=True),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_bases_status"), "knowledge_bases", ["status"], unique=False)
    op.create_index(op.f("ix_knowledge_bases_tenant_id"), "knowledge_bases", ["tenant_id"], unique=False)

    op.create_table(
        "tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("handler_type", sa.String(length=32), nullable=False, server_default="builtin"),
        sa.Column("input_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("handler_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("version", sa.String(length=32), nullable=False, server_default="1.0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_tools_tenant_slug"),
    )
    op.create_index(op.f("ix_tools_slug"), "tools", ["slug"], unique=False)
    op.create_index(op.f("ix_tools_status"), "tools", ["status"], unique=False)
    op.create_index(op.f("ix_tools_tenant_id"), "tools", ["tenant_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False, server_default="system"),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_id"), "audit_logs", ["resource_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_type"), "audit_logs", ["resource_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_tenant_id"), "audit_logs", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_tenant_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_tools_tenant_id"), table_name="tools")
    op.drop_index(op.f("ix_tools_status"), table_name="tools")
    op.drop_index(op.f("ix_tools_slug"), table_name="tools")
    op.drop_table("tools")

    op.drop_index(op.f("ix_knowledge_bases_tenant_id"), table_name="knowledge_bases")
    op.drop_index(op.f("ix_knowledge_bases_status"), table_name="knowledge_bases")
    op.drop_table("knowledge_bases")

    op.drop_index(op.f("ix_agent_configurations_tenant_id"), table_name="agent_configurations")
    op.drop_index(op.f("ix_agent_configurations_agent_id"), table_name="agent_configurations")
    op.drop_table("agent_configurations")

    op.drop_index(op.f("ix_agents_tenant_id"), table_name="agents")
    op.drop_index(op.f("ix_agents_status"), table_name="agents")
    op.drop_table("agents")

    op.drop_index(op.f("ix_tenants_status"), table_name="tenants")
    op.drop_index(op.f("ix_tenants_slug"), table_name="tenants")
    op.drop_table("tenants")
