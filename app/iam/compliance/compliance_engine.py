"""Compliance framework abstractions."""

from app.core.enums import ComplianceFramework


class ComplianceEngine:
    """Prepares compliance configuration — extensible for GDPR, HIPAA, SOC2, etc."""

    SUPPORTED = frozenset(ComplianceFramework)

    def validate_frameworks(self, frameworks: list[str]) -> list[str]:
        violations = []
        for f in frameworks:
            if f not in self.SUPPORTED:
                violations.append(f"unsupported_framework:{f}")
        return violations

    def default_settings(self, frameworks: list[str]) -> dict:
        settings: dict = {"right_to_delete_enabled": True}
        if ComplianceFramework.GDPR in frameworks:
            settings["consent_management"] = {"required": True, "granular": True}
        if ComplianceFramework.HIPAA in frameworks:
            settings["data_residency"] = settings.get("data_residency", "us")
            settings["encryption_required"] = True
        if ComplianceFramework.PCI_DSS in frameworks:
            settings["mfa_required"] = True
        return settings
