"""Enterprise planner agent ORM models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import PlannerDecisionStatus, PlannerSessionStatus
from app.database.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class PlannerSessionModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Planner reasoning session bound to a conversation."""

    __tablename__ = "planner_sessions"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=PlannerSessionStatus.ACTIVE,
        index=True,
    )
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    reasoning_step_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    decisions = relationship("PlannerDecisionModel", back_populates="session", cascade="all, delete-orphan")
    history = relationship("PlannerHistoryModel", back_populates="session", cascade="all, delete-orphan")


class PlannerDecisionModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Structured planner decision output."""

    __tablename__ = "planner_decisions"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("planner_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    intent: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    next_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=PlannerDecisionStatus.COMPLETED,
        index=True,
    )
    reasoning_steps: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tool_call: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_decisions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    model_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="structured")
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    session = relationship("PlannerSessionModel", back_populates="decisions")


class PlannerHistoryModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Append-only planner reasoning history."""

    __tablename__ = "planner_history"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("planner_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("planner_decisions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session = relationship("PlannerSessionModel", back_populates="history")


class PlannerMetricsModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Aggregated planner metrics snapshot."""

    __tablename__ = "planner_metrics"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    total_plans: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    escalation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    average_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    average_reasoning_steps: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cache_hits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_misses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    calls_by_intent: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
