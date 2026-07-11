"""Enterprise IAM ORM models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OrganizationModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Organization profile — 1:1 with tenant for IAM."""

    __tablename__ = "organizations"

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(32), nullable=False, default="free")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    branding: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    security_policy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    billing: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    memberships = relationship("OrganizationMembershipModel", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("IamApiKeyModel", back_populates="organization", cascade="all, delete-orphan")
    roles = relationship("IamRoleModel", back_populates="organization", cascade="all, delete-orphan")


class IamUserModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "iam_users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    memberships = relationship("OrganizationMembershipModel", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("IamSessionModel", back_populates="user", cascade="all, delete-orphan")
    mfa_factors = relationship("MfaFactorModel", back_populates="user", cascade="all, delete-orphan")
    oauth_identities = relationship("OAuthIdentityModel", back_populates="user", cascade="all, delete-orphan")


class OrganizationMembershipModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organization_memberships"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_org_membership_user"),)

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("iam_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_slug: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization = relationship("OrganizationModel", back_populates="memberships")
    user = relationship("IamUserModel", back_populates="memberships")


class IamRoleModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "iam_roles"
    __table_args__ = (UniqueConstraint("organization_id", "slug", name="uq_iam_roles_org_slug"),)

    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    inherits_from: Mapped[list[str] | None] = mapped_column(ARRAY(String(64)), nullable=True)
    permissions: Mapped[list[str] | None] = mapped_column(ARRAY(String(64)), nullable=True)

    organization = relationship("OrganizationModel", back_populates="roles")


class IamApiKeyModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "iam_api_keys"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    scopes: Mapped[list[str] | None] = mapped_column(ARRAY(String(64)), nullable=True)
    permissions: Mapped[list[str] | None] = mapped_column(ARRAY(String(64)), nullable=True)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="production")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    organization = relationship("OrganizationModel", back_populates="api_keys")


class IamSessionModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "iam_sessions"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("iam_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    refresh_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("IamUserModel", back_populates="sessions")


class IamSecurityPolicyModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "iam_security_policies"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    password_min_length: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    session_timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=3600)
    mfa_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allowed_domains: Mapped[list[str] | None] = mapped_column(ARRAY(String(255)), nullable=True)
    ip_allowlist: Mapped[list[str] | None] = mapped_column(ARRAY(String(45)), nullable=True)
    rate_limits: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    api_limits: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    data_retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class IamSecurityEventModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "iam_security_events"

    organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("iam_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="info")
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class IamAuditLogModel(Base, UUIDPrimaryKeyMixin):
    """Immutable IAM audit trail — append only."""

    __tablename__ = "iam_audit_logs"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False, default="user")
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class OAuthIdentityModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "oauth_identities"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("iam_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("IamUserModel", back_populates="oauth_identities")


class SsoProviderModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sso_providers"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class MfaFactorModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mfa_factors"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("iam_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    factor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    backup_codes_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("IamUserModel", back_populates="mfa_factors")


class ComplianceSettingsModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "compliance_settings"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    frameworks: Mapped[list[str] | None] = mapped_column(ARRAY(String(32)), nullable=True)
    data_residency: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consent_management: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    right_to_delete_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
