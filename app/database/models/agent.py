"""Agent ORM model."""

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AgentStatus
from app.database.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AgentModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Voice AI agent owned by a tenant."""

    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    voice: Mapped[str] = mapped_column(String(64), nullable=False, default="default")
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en-US")
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    max_reasoning_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    planner_model: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    verifier_model: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=AgentStatus.DRAFT,
        index=True,
    )

    tenant = relationship("TenantModel", back_populates="agents")
    configuration = relationship(
        "AgentConfigurationModel",
        back_populates="agent",
        uselist=False,
        cascade="all, delete-orphan",
    )
