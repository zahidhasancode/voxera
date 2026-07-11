"""Configuration domain — Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.core.schemas import SchemaBase, TenantScopedSchema, TimestampSchema


class AgentConfigurationCreate(TenantScopedSchema):
    agent_id: UUID
    identity_verification_enabled: bool = False
    escalation_rules: dict | None = None
    fallback_message: str | None = None
    allowed_tool_ids: list[UUID] | None = None
    working_hours: dict | None = None
    response_tone: str | None = Field(default=None, max_length=64)
    max_conversation_length: int | None = Field(default=None, ge=1)
    extra_settings: dict | None = None


class AgentConfigurationUpdate(SchemaBase):
    identity_verification_enabled: bool | None = None
    escalation_rules: dict | None = None
    fallback_message: str | None = None
    allowed_tool_ids: list[UUID] | None = None
    working_hours: dict | None = None
    response_tone: str | None = Field(default=None, max_length=64)
    max_conversation_length: int | None = Field(default=None, ge=1)
    extra_settings: dict | None = None


class AgentConfigurationRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    agent_id: UUID
    identity_verification_enabled: bool
    escalation_rules: dict | None
    fallback_message: str | None
    allowed_tool_ids: list[UUID] | None
    working_hours: dict | None
    response_tone: str | None
    max_conversation_length: int | None
    extra_settings: dict | None
