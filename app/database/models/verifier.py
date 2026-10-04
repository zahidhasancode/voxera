"""Enterprise verifier agent ORM models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class VerifierDecisionModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Persistent verifier decision record."""

    __tablename__ = "verifier_decisions"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    planner_decision_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    approved: Mapped[bool] = mapped_column(nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    requires_confirmation: Mapped[bool] = mapped_column(nullable=False, default=False)
    requires_human: Mapped[bool] = mapped_column(nullable=False, default=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_tool_arguments: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    warnings: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    violations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    planner_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    identity_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="structured")
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class RiskAssessmentModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Risk assessment attached to a verifier decision."""

    __tablename__ = "verifier_risk_assessments"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    decision_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("verifier_decisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tool_slug: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    factors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class PolicyViolationModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Recorded policy violations."""

    __tablename__ = "verifier_policy_violations"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    decision_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("verifier_decisions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    policy_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    violation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class ComplianceCheckModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Compliance framework check results."""

    __tablename__ = "verifier_compliance_checks"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    decision_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("verifier_decisions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    framework: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    passed: Mapped[bool] = mapped_column(nullable=False)
    findings: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class VerifierAuditModel(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """Immutable verifier audit trail."""

    __tablename__ = "verifier_audit_logs"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    decision_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("verifier_decisions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    planner_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    verifier_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validation_failures: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    policy_violations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    identity_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tool_validation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
