"""Agent configuration ORM model."""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AgentConfigurationModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Per-agent behavioral configuration (1:1 with agent)."""

    __tablename__ = "agent_configurations"
    __table_args__ = (UniqueConstraint("agent_id", name="uq_agent_configurations_agent_id"),)

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    identity_verification_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    escalation_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    fallback_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    allowed_tool_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    working_hours: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_tone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    max_conversation_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extra_settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    agent = relationship("AgentModel", back_populates="configuration")
