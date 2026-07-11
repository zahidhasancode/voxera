"""Tool registry CRUD Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.core.enums import ToolHandlerType, ToolStatus
from app.core.schemas import SchemaBase, TenantScopedSchema, TimestampSchema


class ToolCreate(TenantScopedSchema):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=2, max_length=128, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = Field(default=None, max_length=2000)
    handler_type: ToolHandlerType
    handler_config: dict | None = None
    input_schema: dict | None = None
    status: ToolStatus = ToolStatus.ACTIVE
    version: str = Field(default="1.0.0", max_length=32)


class ToolUpdate(SchemaBase):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    handler_type: ToolHandlerType | None = None
    handler_config: dict | None = None
    input_schema: dict | None = None
    status: ToolStatus | None = None
    version: str | None = Field(default=None, max_length=32)


class ToolRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    name: str
    slug: str
    description: str | None
    handler_type: ToolHandlerType
    handler_config: dict | None
    input_schema: dict | None
    status: ToolStatus
    version: str
