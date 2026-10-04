"""Memory subsystem ORM models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ConversationStatus, SessionState, ToolExecutionStatus
from app.database.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ConversationModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Active or archived voice/chat session."""

    __tablename__ = "conversations"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ConversationStatus.ACTIVE,
        index=True,
    )
    current_state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=SessionState.CALL_STARTED,
        index=True,
    )
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    turns = relationship("ConversationTurnModel", back_populates="conversation", cascade="all, delete-orphan")
    summaries = relationship(
        "ConversationSummaryModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    working_memory = relationship(
        "WorkingMemoryModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    tool_executions = relationship(
        "ToolExecutionModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class ConversationTurnModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Single conversation turn."""

    __tablename__ = "conversation_turns"

    conversation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tool_calls: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    reasoning_steps: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    conversation = relationship("ConversationModel", back_populates="turns")


class ConversationSummaryModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Structured conversation summary for token-efficient planner context."""

    __tablename__ = "conversation_summaries"

    conversation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_identity: Mapped[str | None] = mapped_column(Text, nullable=True)
    conversation_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_items: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    pending_items: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    collected_information: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    turn_count_at_summary: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")

    conversation = relationship("ConversationModel", back_populates="summaries")


class WorkingMemoryModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Temporary session-scoped key-value memory."""

    __tablename__ = "working_memory"
    __table_args__ = (
        UniqueConstraint("conversation_id", "memory_key", name="uq_working_memory_conversation_key"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    memory_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(32), nullable=False, default="string")
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_sensitive: Mapped[bool] = mapped_column(nullable=False, default=False)

    conversation = relationship("ConversationModel", back_populates="working_memory")


class ToolExecutionModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Persisted tool execution for planner reuse."""

    __tablename__ = "tool_executions"

    conversation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    arguments: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ToolExecutionStatus.SUCCESS,
        index=True,
    )
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation = relationship("ConversationModel", back_populates="tool_executions")
