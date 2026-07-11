"""Security policy engine tests."""

from datetime import datetime, timezone

import pytest

from app.core.exceptions import SecurityPolicyViolationError
from app.iam.policies.security_policy_engine import SecurityPolicyEngine
from app.iam.schemas import SecurityPolicyRead


def _policy(**kwargs) -> SecurityPolicyRead:
    now = datetime.now(timezone.utc)
    return SecurityPolicyRead(
        organization_id=kwargs.get("organization_id", __import__("uuid").uuid4()),
        password_min_length=12,
        session_timeout_seconds=3600,
        mfa_required=False,
        allowed_domains=kwargs.get("allowed_domains", []),
        ip_allowlist=kwargs.get("ip_allowlist", []),
        created_at=now,
        updated_at=now,
    )


def test_email_domain_allowed():
    engine = SecurityPolicyEngine()
    engine.validate_email_domain(_policy(allowed_domains=["acme.com"]), "user@acme.com")


def test_email_domain_rejected():
    engine = SecurityPolicyEngine()
    with pytest.raises(SecurityPolicyViolationError):
        engine.validate_email_domain(_policy(allowed_domains=["acme.com"]), "user@gmail.com")


def test_password_min_length():
    engine = SecurityPolicyEngine()
    with pytest.raises(SecurityPolicyViolationError):
        engine.validate_password(_policy(), "short")
