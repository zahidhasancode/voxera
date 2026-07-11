"""Tool registry ORM model."""

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ToolHandlerType, ToolStatus
from app.database.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ToolModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Registered tool / function available to agents within a tenant."""

    __tablename__ = "tools"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_tools_tenant_slug"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    handler_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ToolHandlerType.BUILTIN,
    )
    input_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    handler_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ToolStatus.ACTIVE,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")

    tenant = relationship("TenantModel", back_populates="tools")
