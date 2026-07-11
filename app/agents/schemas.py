"""Agent domain — Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.core.enums import AgentStatus
from app.core.schemas import SchemaBase, TenantScopedSchema, TimestampSchema


class AgentCreate(TenantScopedSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    system_prompt: str = Field(..., min_length=1)
    voice: str = Field(default="alloy", max_length=64)
    language: str = Field(default="en", max_length=16)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_reasoning_steps: int = Field(default=5, ge=1, le=50)
    planner_model: str | None = Field(default=None, max_length=128)
    verifier_model: str | None = Field(default=None, max_length=128)
    status: AgentStatus = AgentStatus.DRAFT


class AgentUpdate(SchemaBase):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    system_prompt: str | None = Field(default=None, min_length=1)
    voice: str | None = Field(default=None, max_length=64)
    language: str | None = Field(default=None, max_length=16)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_reasoning_steps: int | None = Field(default=None, ge=1, le=50)
    planner_model: str | None = Field(default=None, max_length=128)
    verifier_model: str | None = Field(default=None, max_length=128)
    status: AgentStatus | None = None


class AgentRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    name: str
    description: str | None
    system_prompt: str
    voice: str
    language: str
    temperature: float
    max_reasoning_steps: int
    planner_model: str | None
    verifier_model: str | None
    status: AgentStatus
