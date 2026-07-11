"""Knowledge base domain schemas (Sprint 1 legacy container)."""

from uuid import UUID

from pydantic import Field

from app.core.enums import KnowledgeBaseStatus
from app.core.schemas import SchemaBase, TenantScopedSchema, TimestampSchema


class KnowledgeBaseCreate(TenantScopedSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    status: KnowledgeBaseStatus = KnowledgeBaseStatus.PROCESSING
    embedding_model: str | None = Field(default=None, max_length=128)
    settings: dict | None = None


class KnowledgeBaseUpdate(SchemaBase):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    status: KnowledgeBaseStatus | None = None
    embedding_model: str | None = Field(default=None, max_length=128)
    settings: dict | None = None


class KnowledgeBaseRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    name: str
    description: str | None
    status: KnowledgeBaseStatus
    embedding_model: str | None
    settings: dict | None
