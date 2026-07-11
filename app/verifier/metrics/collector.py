"""Verifier observability metrics."""

from dataclasses import dataclass, field

from app.verifier.schemas import VerifierMetricsSnapshot


@dataclass
class VerifierMetricsCollector:
    total_verifications: int = 0
    approval_count: int = 0
    rejection_count: int = 0
    escalation_count: int = 0
    confirmation_required_count: int = 0
    total_latency_ms: float = 0.0
    hallucination_count: int = 0
    policy_rejection_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_tokens: int = 0
    risk_distribution: dict[str, int] = field(default_factory=dict)

    def record(
        self,
        *,
        approved: bool,
        outcome: str,
        latency_ms: float,
        tokens: int,
        violations: list[str],
        risk: str,
    ) -> None:
        self.total_verifications += 1
        self.total_latency_ms += latency_ms
        self.total_tokens += tokens
        self.risk_distribution[risk] = self.risk_distribution.get(risk, 0) + 1

        if any("hallucin" in v for v in violations):
            self.hallucination_count += 1
        if any("blocked" in v or "policy" in v or "not_allowed" in v for v in violations):
            self.policy_rejection_count += 1

        if outcome == "approved":
            self.approval_count += 1
        elif outcome == "rejected":
            self.rejection_count += 1
        elif outcome == "escalated":
            self.escalation_count += 1
        elif outcome == "requires_confirmation":
            self.confirmation_required_count += 1
        elif not approved:
            self.rejection_count += 1
        else:
            self.approval_count += 1

    def snapshot(self) -> VerifierMetricsSnapshot:
        n = self.total_verifications or 1
        return VerifierMetricsSnapshot(
            total_verifications=self.total_verifications,
            approval_count=self.approval_count,
            rejection_count=self.rejection_count,
            escalation_count=self.escalation_count,
            confirmation_required_count=self.confirmation_required_count,
            average_latency_ms=self.total_latency_ms / n if self.total_verifications else 0.0,
            hallucination_rate=self.hallucination_count / n if self.total_verifications else 0.0,
            policy_rejection_rate=self.policy_rejection_count / n if self.total_verifications else 0.0,
            approval_rate=self.approval_count / n if self.total_verifications else 0.0,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses,
            total_tokens=self.total_tokens,
            risk_distribution=dict(self.risk_distribution),
        )
