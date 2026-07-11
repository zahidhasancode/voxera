"""Organization security policy evaluation."""

from app.core.exceptions import SecurityPolicyViolationError
from app.iam.schemas import SecurityPolicyRead


class SecurityPolicyEngine:
    def validate_email_domain(self, policy: SecurityPolicyRead, email: str) -> None:
        if not policy.allowed_domains:
            return
        domain = email.split("@")[-1].lower()
        if domain not in {d.lower() for d in policy.allowed_domains}:
            raise SecurityPolicyViolationError(
                f"Email domain not allowed: {domain}",
                violations=["domain_not_allowed"],
            )

    def validate_password(self, policy: SecurityPolicyRead, password: str) -> None:
        if len(password) < policy.password_min_length:
            raise SecurityPolicyViolationError(
                "Password does not meet minimum length",
                violations=["password_too_short"],
            )

    def validate_ip(self, policy: SecurityPolicyRead, ip: str | None) -> None:
        if not policy.ip_allowlist or not ip:
            return
        if ip not in policy.ip_allowlist:
            raise SecurityPolicyViolationError(
                "IP address not in allow list",
                violations=["ip_not_allowed"],
            )
