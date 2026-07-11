"""Knowledge ingestion schema tables.

Revision ID: 002_knowledge_ingestion
Revises: 001_initial_enterprise
Create Date: 2026-07-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_knowledge_ingestion"
down_revision: Union[str, None] = "001_initial_enterprise"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("website_url", sa.String(length=2048), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("original_filename", sa.String(length=512), nullable=True),
        sa.Column("processing_stage", sa.String(length=32), nullable=True),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding_model", sa.String(length=128), nullable=True),
        sa.Column("embedding_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("vector_namespace", sa.String(length=256), nullable=False),
        sa.Column("vector_store_type", sa.String(length=32), nullable=True),
        sa.Column("chunk_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vector_namespace"),
    )
    op.create_index(op.f("ix_knowledge_sources_source_type"), "knowledge_sources", ["source_type"], unique=False)
    op.create_index(op.f("ix_knowledge_sources_status"), "knowledge_sources", ["status"], unique=False)
    op.create_index(op.f("ix_knowledge_sources_processing_stage"), "knowledge_sources", ["processing_stage"], unique=False)
    op.create_index(op.f("ix_knowledge_sources_embedding_status"), "knowledge_sources", ["embedding_status"], unique=False)
    op.create_index(op.f("ix_knowledge_sources_tenant_id"), "knowledge_sources", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_knowledge_sources_vector_namespace"), "knowledge_sources", ["vector_namespace"], unique=False)

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("char_count", sa.Integer(), nullable=True),
        sa.Column("vector_id", sa.String(length=256), nullable=True),
        sa.Column("chunk_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["knowledge_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_chunks_source_id"), "knowledge_chunks", ["source_id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunks_tenant_id"), "knowledge_chunks", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunks_vector_id"), "knowledge_chunks", ["vector_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_chunks_vector_id"), table_name="knowledge_chunks")
    op.drop_index(op.f("ix_knowledge_chunks_tenant_id"), table_name="knowledge_chunks")
    op.drop_index(op.f("ix_knowledge_chunks_source_id"), table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")

    op.drop_index(op.f("ix_knowledge_sources_vector_namespace"), table_name="knowledge_sources")
    op.drop_index(op.f("ix_knowledge_sources_tenant_id"), table_name="knowledge_sources")
    op.drop_index(op.f("ix_knowledge_sources_embedding_status"), table_name="knowledge_sources")
    op.drop_index(op.f("ix_knowledge_sources_processing_stage"), table_name="knowledge_sources")
    op.drop_index(op.f("ix_knowledge_sources_status"), table_name="knowledge_sources")
    op.drop_index(op.f("ix_knowledge_sources_source_type"), table_name="knowledge_sources")
    op.drop_table("knowledge_sources")
