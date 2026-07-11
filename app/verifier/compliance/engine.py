"""Compliance framework abstraction — provider-independent."""

from abc import ABC, abstractmethod

from app.core.enums import ComplianceFramework
from app.verifier.schemas import ValidationContext


class ComplianceChecker(ABC):
    @property
    @abstractmethod
    def framework(self) -> ComplianceFramework:
        ...

    @abstractmethod
    def check(self, ctx: ValidationContext) -> tuple[bool, list[str]]:
        ...


class GdprComplianceChecker(ComplianceChecker):
    @property
    def framework(self) -> ComplianceFramework:
        return ComplianceFramework.GDPR

    def check(self, ctx: ValidationContext) -> tuple[bool, list[str]]:
        findings: list[str] = []
        policies = ctx.verifier_input.tenant_policies
        if not policies.get("gdpr_enabled", True):
            return True, findings

        plan = ctx.verifier_input.planner_output
        if plan.tool_call and plan.tool_call.tool_slug in ("crm_lookup", "crm_update", "email", "sms"):
            if ctx.identity_status.value != "verified" and ctx.verifier_input.working_memory.get("consent_given") != "true":
                findings.append("gdpr:personal_data_processing_without_consent_or_verification")

        return len(findings) == 0, findings


class HipaaComplianceChecker(ComplianceChecker):
    @property
    def framework(self) -> ComplianceFramework:
        return ComplianceFramework.HIPAA

    def check(self, ctx: ValidationContext) -> tuple[bool, list[str]]:
        findings: list[str] = []
        if ctx.verifier_input.industry != "healthcare":
            return True, findings

        plan = ctx.verifier_input.planner_output
        phi_tools = {"appointment", "crm_lookup", "crm_update"}
        if plan.tool_call and plan.tool_call.tool_slug in phi_tools:
            if ctx.identity_status.value != "verified":
                findings.append("hipaa:phi_access_without_verified_identity")

        return len(findings) == 0, findings


class PciDssComplianceChecker(ComplianceChecker):
    @property
    def framework(self) -> ComplianceFramework:
        return ComplianceFramework.PCI_DSS

    def check(self, ctx: ValidationContext) -> tuple[bool, list[str]]:
        findings: list[str] = []
        if ctx.verifier_input.industry not in ("banking", "finance", None):
            policies = ctx.verifier_input.tenant_policies
            if not policies.get("pci_enabled"):
                return True, findings

        args_str = str(ctx.verifier_input.planner_output.tool_call.arguments if ctx.verifier_input.planner_output.tool_call else {})
        if any(k in args_str.lower() for k in ("card_number", "cvv", "pan")):
            findings.append("pci:raw_payment_data_in_tool_arguments")

        return len(findings) == 0, findings


class Soc2ComplianceChecker(ComplianceChecker):
    @property
    def framework(self) -> ComplianceFramework:
        return ComplianceFramework.SOC2

    def check(self, ctx: ValidationContext) -> tuple[bool, list[str]]:
        findings: list[str] = []
        if ctx.violations:
            findings.append("soc2:control_failure_detected_in_validation")
        return len(findings) == 0, findings


class Iso27001ComplianceChecker(ComplianceChecker):
    @property
    def framework(self) -> ComplianceFramework:
        return ComplianceFramework.ISO27001

    def check(self, ctx: ValidationContext) -> tuple[bool, list[str]]:
        findings: list[str] = []
        plan = ctx.verifier_input.planner_output
        if plan.tool_call and plan.tool_call.tool_slug == "webhook":
            findings.append("iso27001:external_integration_requires_review")
        return len(findings) == 0, findings


class ComplianceEngine:
    def __init__(self, checkers: list[ComplianceChecker] | None = None) -> None:
        self._checkers = checkers or [
            GdprComplianceChecker(),
            HipaaComplianceChecker(),
            PciDssComplianceChecker(),
            Soc2ComplianceChecker(),
            Iso27001ComplianceChecker(),
        ]

    def evaluate(self, ctx: ValidationContext, *, enabled_frameworks: list[str] | None = None) -> list[str]:
        violations: list[str] = []
        enabled = set(enabled_frameworks or [f.value for f in ComplianceFramework])
        all_passed = True

        for checker in self._checkers:
            if checker.framework.value not in enabled:
                continue
            passed, findings = checker.check(ctx)
            if not passed:
                all_passed = False
                violations.extend(findings)
                ctx.compliance_findings.extend(findings)

        ctx.compliance_passed = all_passed and not violations
        return violations
