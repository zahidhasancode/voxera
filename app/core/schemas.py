"""Shared Pydantic schema primitives."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TimestampSchema(SchemaBase):
    created_at: datetime
    updated_at: datetime


class TenantScopedSchema(SchemaBase):
    tenant_id: UUID


class PaginationParams(SchemaBase):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)


class PaginatedResponse(SchemaBase):
    total: int
    offset: int
    limit: int
