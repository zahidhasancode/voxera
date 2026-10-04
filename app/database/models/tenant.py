"""Tenant ORM model."""

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import SubscriptionPlan, TenantStatus
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TenantModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Company / organization — root of multi-tenant isolation."""

    __tablename__ = "tenants"

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    contact_email: Mapped[str] = mapped_column(String(320), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    languages: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)),
        nullable=False,
        default=list,
        server_default="{}",
    )
    subscription_plan: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=SubscriptionPlan.FREE,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=TenantStatus.ACTIVE,
        index=True,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    agents = relationship("AgentModel", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_bases = relationship(
        "KnowledgeBaseModel",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    knowledge_sources = relationship(
        "KnowledgeSourceModel",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    tools = relationship("ToolModel", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogModel", back_populates="tenant", cascade="all, delete-orphan")
