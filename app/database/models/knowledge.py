"""Knowledge base ORM model."""

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import KnowledgeBaseStatus
from app.database.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeBaseModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Tenant-scoped knowledge repository for RAG / agent context."""

    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=KnowledgeBaseStatus.PROCESSING,
        index=True,
    )
    embedding_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    tenant = relationship("TenantModel", back_populates="knowledge_bases")
