"""AI evaluation metrics for golden dataset runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationCaseResult:
    case_id: str
    domain: str
    passed: bool
    intent_match: bool | None = None
    intent_expected: str | None = None
    intent_actual: str | None = None
    verifier_approval_match: bool | None = None
    tool_match: bool | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class EvaluationReport:
    version: str
    domain: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    intent_accuracy: float = 0.0
    verifier_accuracy: float = 0.0
    tool_selection_accuracy: float = 0.0
    results: list[EvaluationCaseResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total * 100.0) if self.total else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "domain": self.domain,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate_pct": round(self.pass_rate, 2),
            "intent_accuracy_pct": round(self.intent_accuracy * 100, 2),
            "verifier_accuracy_pct": round(self.verifier_accuracy * 100, 2),
            "tool_selection_accuracy_pct": round(self.tool_selection_accuracy * 100, 2),
            "results": [
                {
                    "case_id": r.case_id,
                    "passed": r.passed,
                    "intent_match": r.intent_match,
                    "intent_expected": r.intent_expected,
                    "intent_actual": r.intent_actual,
                    "notes": r.notes,
                }
                for r in self.results
            ],
        }


def compute_intent_accuracy(results: list[EvaluationCaseResult]) -> float:
    scored = [r for r in results if r.intent_match is not None]
    if not scored:
        return 0.0
    return sum(1 for r in scored if r.intent_match) / len(scored)


def compute_verifier_accuracy(results: list[EvaluationCaseResult]) -> float:
    scored = [r for r in results if r.verifier_approval_match is not None]
    if not scored:
        return 0.0
    return sum(1 for r in scored if r.verifier_approval_match) / len(scored)


def compute_tool_accuracy(results: list[EvaluationCaseResult]) -> float:
    scored = [r for r in results if r.tool_match is not None]
    if not scored:
        return 0.0
    return sum(1 for r in scored if r.tool_match) / len(scored)


def build_report(version: str, domain: str, results: list[EvaluationCaseResult]) -> EvaluationReport:
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    return EvaluationReport(
        version=version,
        domain=domain,
        total=len(results),
        passed=passed,
        failed=failed,
        intent_accuracy=compute_intent_accuracy(results),
        verifier_accuracy=compute_verifier_accuracy(results),
        tool_selection_accuracy=compute_tool_accuracy(results),
        results=results,
    )
