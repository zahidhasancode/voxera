"""Tenant domain — Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.core.enums import SubscriptionPlan, TenantStatus
from app.core.schemas import SchemaBase, TimestampSchema


class TenantCreate(SchemaBase):
    company_name: str = Field(..., min_length=1, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    slug: str = Field(..., min_length=2, max_length=128, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    contact_email: EmailStr
    timezone: str = Field(default="UTC", max_length=64)
    languages: list[str] = Field(default_factory=lambda: ["en"])
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    status: TenantStatus = TenantStatus.ACTIVE
    metadata: dict | None = None


class TenantUpdate(SchemaBase):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    contact_email: EmailStr | None = None
    timezone: str | None = Field(default=None, max_length=64)
    languages: list[str] | None = None
    subscription_plan: SubscriptionPlan | None = None
    status: TenantStatus | None = None
    metadata: dict | None = None


class TenantRead(TimestampSchema):
    id: UUID
    company_name: str
    industry: str | None
    slug: str
    contact_email: EmailStr
    timezone: str
    languages: list[str]
    subscription_plan: SubscriptionPlan
    status: TenantStatus
    metadata: dict | None = Field(default=None, validation_alias="metadata_")
