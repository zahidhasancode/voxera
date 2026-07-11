"""009 — Knowledge production schema: vectors, ingestion jobs, indexes."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_knowledge_production"
down_revision: Union[str, None] = "008_enterprise_iam"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_vectors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("namespace", sa.String(length=256), nullable=False),
        sa.Column("vector_id", sa.String(length=256), nullable=False),
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("namespace", "vector_id", name="uq_knowledge_vectors_namespace_vector_id"),
    )
    op.create_index("ix_knowledge_vectors_namespace", "knowledge_vectors", ["namespace"])

    op.create_table(
        "knowledge_ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("stage", sa.String(length=32), nullable=True),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("worker_id", sa.String(length=64), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["knowledge_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_ingestion_jobs_tenant_id", "knowledge_ingestion_jobs", ["tenant_id"])
    op.create_index("ix_knowledge_ingestion_jobs_source_id", "knowledge_ingestion_jobs", ["source_id"])
    op.create_index("ix_knowledge_ingestion_jobs_status", "knowledge_ingestion_jobs", ["status"])

    op.add_column("knowledge_sources", sa.Column("file_hash", sa.String(length=64), nullable=True))
    op.create_index("ix_knowledge_sources_file_hash", "knowledge_sources", ["file_hash"])
    op.create_index(
        "ix_knowledge_chunks_tenant_source",
        "knowledge_chunks",
        ["tenant_id", "source_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_tenant_source", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_sources_file_hash", table_name="knowledge_sources")
    op.drop_column("knowledge_sources", "file_hash")
    op.drop_table("knowledge_ingestion_jobs")
    op.drop_index("ix_knowledge_vectors_namespace", table_name="knowledge_vectors")
    op.drop_table("knowledge_vectors")
