"""Audit log domain — Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.core.enums import AuditActorType
from app.core.schemas import SchemaBase, TenantScopedSchema


class AuditLogCreate(TenantScopedSchema):
    action: str = Field(..., min_length=1, max_length=128)
    actor_type: AuditActorType
    actor_id: str | None = Field(default=None, max_length=255)
    resource_type: str = Field(..., min_length=1, max_length=64)
    resource_id: UUID | None = None
    metadata: dict | None = None
    ip_address: str | None = Field(default=None, max_length=45)


class AuditLogRead(TenantScopedSchema):
    id: UUID
    action: str
    actor_type: AuditActorType
    actor_id: str | None
    resource_type: str
    resource_id: UUID | None
    metadata: dict | None = Field(default=None, validation_alias="metadata_")
    ip_address: str | None
    created_at: datetime


class AuditLogFilter(SchemaBase):
    action: str | None = None
    actor_type: AuditActorType | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    since: datetime | None = None
    until: datetime | None = None
