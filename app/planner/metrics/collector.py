"""Planner observability metrics."""

from dataclasses import dataclass, field

from app.planner.schemas import PlannerMetricsSnapshot


@dataclass
class PlannerMetricsCollector:
    total_plans: int = 0
    success_count: int = 0
    failure_count: int = 0
    escalation_count: int = 0
    total_latency_ms: float = 0.0
    total_confidence: float = 0.0
    total_reasoning_steps: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_tokens: int = 0
    calls_by_intent: dict[str, int] = field(default_factory=dict)

    def record_plan(
        self,
        *,
        intent: str,
        success: bool,
        latency_ms: float,
        confidence: float,
        reasoning_steps: int,
        tokens: int,
        escalated: bool = False,
    ) -> None:
        self.total_plans += 1
        self.total_latency_ms += latency_ms
        self.total_confidence += confidence
        self.total_reasoning_steps += reasoning_steps
        self.total_tokens += tokens
        self.calls_by_intent[intent] = self.calls_by_intent.get(intent, 0) + 1
        if escalated:
            self.escalation_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        self.cache_misses += 1

    def snapshot(self) -> PlannerMetricsSnapshot:
        n = self.total_plans or 1
        return PlannerMetricsSnapshot(
            total_plans=self.total_plans,
            success_count=self.success_count,
            failure_count=self.failure_count,
            escalation_count=self.escalation_count,
            average_latency_ms=self.total_latency_ms / n if self.total_plans else 0.0,
            average_confidence=self.total_confidence / n if self.total_plans else 0.0,
            average_reasoning_steps=self.total_reasoning_steps / n if self.total_plans else 0.0,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses,
            total_tokens=self.total_tokens,
            calls_by_intent=dict(self.calls_by_intent),
        )

    def merge_db(self, db: dict) -> PlannerMetricsSnapshot:
        local = self.snapshot()
        total = local.total_plans + db.get("total_plans", 0)
        if not total:
            return local
        return PlannerMetricsSnapshot(
            total_plans=total,
            success_count=local.success_count + db.get("success_count", 0),
            failure_count=local.failure_count + db.get("failure_count", 0),
            escalation_count=local.escalation_count + db.get("escalation_count", 0),
            average_latency_ms=(local.average_latency_ms * local.total_plans + db.get("average_latency_ms", 0) * db.get("total_plans", 0)) / total,
            average_confidence=(local.average_confidence * local.total_plans + db.get("average_confidence", 0) * db.get("total_plans", 0)) / total,
            average_reasoning_steps=(local.average_reasoning_steps * local.total_plans + db.get("average_reasoning_steps", 0) * db.get("total_plans", 0)) / total,
            cache_hits=local.cache_hits + db.get("cache_hits", 0),
            cache_misses=local.cache_misses + db.get("cache_misses", 0),
            total_tokens=local.total_tokens + db.get("total_tokens", 0),
            calls_by_intent={**db.get("calls_by_intent", {}), **local.calls_by_intent},
        )
