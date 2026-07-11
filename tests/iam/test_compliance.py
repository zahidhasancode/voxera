"""Compliance engine tests."""

from app.core.enums import ComplianceFramework
from app.iam.compliance.compliance_engine import ComplianceEngine


def test_gdpr_settings():
    engine = ComplianceEngine()
    settings = engine.default_settings([ComplianceFramework.GDPR])
    assert settings["consent_management"]["required"] is True


def test_unsupported_framework():
    engine = ComplianceEngine()
    violations = engine.validate_frameworks(["unknown"])
    assert violations
