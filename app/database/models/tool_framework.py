"""Enterprise tool execution framework ORM models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ToolFrameworkExecutionStatus, ToolPermissionEffect
from app.database.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ToolPermissionModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Tenant-scoped allow/block rules for tools."""

    __tablename__ = "tool_permissions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "tool_slug", "agent_id", name="uq_tool_permissions_scope"),
    )

    agent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    tool_slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    effect: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=ToolPermissionEffect.ALLOW,
    )
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    max_executions_per_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    working_hours_start: Mapped[str | None] = mapped_column(String(8), nullable=True)
    working_hours_end: Mapped[str | None] = mapped_column(String(8), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class TenantToolConfigModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Per-tenant tool configuration and credentials references."""

    __tablename__ = "tenant_tool_configs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "tool_slug", name="uq_tenant_tool_configs_slug"),
    )

    tool_slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    credentials_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    provider_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timeout_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class ToolFrameworkExecutionModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Persistent record of tool framework executions (metrics + history)."""

    __tablename__ = "tool_framework_executions"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    tool_slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ToolFrameworkExecutionStatus.SUCCESS,
        index=True,
    )
    arguments: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class ToolAuditModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Immutable audit trail for every tool request and outcome."""

    __tablename__ = "tool_audit_logs"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    execution_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_framework_executions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tool_slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    planner_request: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validated_arguments: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    execution_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    execution_duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    operator: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    execution = relationship("ToolFrameworkExecutionModel", foreign_keys=[execution_id])
