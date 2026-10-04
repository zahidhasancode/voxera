"""IAM Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.core.enums import (
    ApiKeyEnvironment,
    ApiKeyStatus,
    IamSessionStatus,
    IamUserStatus,
    OrganizationStatus,
    SsoProviderType,
    SystemRole,
)
from app.core.schemas import SchemaBase, TimestampSchema


class OrganizationRead(TimestampSchema):
    id: UUID
    tenant_id: UUID
    company_name: str
    slug: str
    plan: str
    status: OrganizationStatus
    region: str | None
    owner_user_id: UUID | None
    timezone: str
    language: str
    branding: dict | None = None
    security_policy: dict | None = None
    billing: dict | None = None


class OrganizationCreate(SchemaBase):
    tenant_id: UUID
    company_name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=2, max_length=128)
    plan: str = "free"
    region: str | None = None
    timezone: str = "UTC"
    language: str = "en"
    owner_user_id: UUID | None = None


class UserRead(TimestampSchema):
    id: UUID
    email: EmailStr
    name: str
    avatar_url: str | None
    status: IamUserStatus
    mfa_enabled: bool
    last_login_at: datetime | None
    role_slug: str | None = None
    department: str | None = None
    title: str | None = None


class UserCreate(SchemaBase):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role_slug: str = SystemRole.VIEWER
    department: str | None = None
    title: str | None = None


class UserInvite(SchemaBase):
    email: EmailStr
    role_slug: str = SystemRole.VIEWER
    department: str | None = None
    title: str | None = None


class LoginRequest(SchemaBase):
    email: EmailStr
    password: str
    organization_id: UUID | None = None


class MagicLinkRequest(SchemaBase):
    email: EmailStr
    organization_id: UUID | None = None


class AuthTokens(SchemaBase):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
    organization_id: UUID | None = None


class RefreshRequest(SchemaBase):
    refresh_token: str = Field(..., min_length=10)


class RegisterRequest(SchemaBase):
    organization: OrganizationCreate
    user: UserCreate


class CurrentUserRead(SchemaBase):
    user: UserRead
    organization_id: UUID
    tenant_id: UUID | None = None
    role_slug: str | None = None
    permissions: list[str] = Field(default_factory=list)


class RoleRead(TimestampSchema):
    id: UUID
    organization_id: UUID | None
    slug: str
    name: str
    description: str | None
    is_system: bool
    inherits_from: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class RoleCreate(SchemaBase):
    slug: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    inherits_from: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class PermissionRead(SchemaBase):
    slug: str
    name: str
    category: str


class ApiKeyRead(TimestampSchema):
    id: UUID
    organization_id: UUID
    name: str
    key_prefix: str
    scopes: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    environment: ApiKeyEnvironment
    status: ApiKeyStatus
    created_by: UUID | None
    last_used_at: datetime | None
    expires_at: datetime | None


class ApiKeyCreate(SchemaBase):
    name: str = Field(..., min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    environment: ApiKeyEnvironment = ApiKeyEnvironment.PRODUCTION
    expires_at: datetime | None = None


class ApiKeyCreateResponse(ApiKeyRead):
    secret: str


class SessionRead(TimestampSchema):
    id: UUID
    user_id: UUID
    organization_id: UUID | None
    browser: str | None
    ip_address: str | None
    country: str | None
    device: str | None
    status: IamSessionStatus
    expires_at: datetime
    revoked_at: datetime | None


class SecurityPolicyRead(TimestampSchema):
    organization_id: UUID
    password_min_length: int
    session_timeout_seconds: int
    mfa_required: bool
    allowed_domains: list[str] = Field(default_factory=list)
    ip_allowlist: list[str] = Field(default_factory=list)
    rate_limits: dict | None = None
    api_limits: dict | None = None
    data_retention_days: int | None = None


class SecurityPolicyUpdate(SchemaBase):
    password_min_length: int | None = None
    session_timeout_seconds: int | None = None
    mfa_required: bool | None = None
    allowed_domains: list[str] | None = None
    ip_allowlist: list[str] | None = None
    rate_limits: dict | None = None
    api_limits: dict | None = None
    data_retention_days: int | None = None


class IamAuditRead(SchemaBase):
    id: UUID
    organization_id: UUID
    actor_user_id: UUID | None
    actor_type: str
    action: str
    resource_type: str
    resource_id: str | None
    ip_address: str | None
    payload: dict | None
    occurred_at: datetime


class SecurityEventRead(TimestampSchema):
    id: UUID
    organization_id: UUID | None
    user_id: UUID | None
    event_type: str
    severity: str
    ip_address: str | None
    payload: dict | None


class SsoProviderRead(TimestampSchema):
    id: UUID
    organization_id: UUID
    provider_type: SsoProviderType
    name: str
    enabled: bool


class ComplianceSettingsRead(TimestampSchema):
    organization_id: UUID
    frameworks: list[str] = Field(default_factory=list)
    data_residency: str | None
    consent_management: dict | None = None
    right_to_delete_enabled: bool


class IamMetricsSnapshot(SchemaBase):
    login_success_count: int = 0
    login_failure_count: int = 0
    active_sessions: int = 0
    api_key_usage_count: int = 0
    permission_checks: int = 0
    security_alerts: int = 0
    policy_violations: int = 0
