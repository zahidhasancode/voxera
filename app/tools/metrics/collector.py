"""In-process tool execution metrics."""

from dataclasses import dataclass, field

from app.tools.schemas.execution import ToolMetricsSnapshot


@dataclass
class ToolMetricsCollector:
    total_executions: int = 0
    success_count: int = 0
    failure_count: int = 0
    permission_denied_count: int = 0
    validation_failure_count: int = 0
    total_latency_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    calls_by_tool: dict[str, int] = field(default_factory=dict)

    def record_execution(
        self,
        *,
        tool_slug: str,
        success: bool,
        latency_ms: float,
        permission_denied: bool = False,
        validation_failed: bool = False,
    ) -> None:
        self.total_executions += 1
        self.total_latency_ms += latency_ms
        self.calls_by_tool[tool_slug] = self.calls_by_tool.get(tool_slug, 0) + 1
        if permission_denied:
            self.permission_denied_count += 1
        elif validation_failed:
            self.validation_failure_count += 1
        elif success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        self.cache_misses += 1

    def snapshot(self) -> ToolMetricsSnapshot:
        avg = self.total_latency_ms / self.total_executions if self.total_executions else 0.0
        rate = self.success_count / self.total_executions if self.total_executions else 0.0
        return ToolMetricsSnapshot(
            total_executions=self.total_executions,
            success_count=self.success_count,
            failure_count=self.failure_count,
            permission_denied_count=self.permission_denied_count,
            validation_failure_count=self.validation_failure_count,
            average_latency_ms=avg,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses,
            calls_by_tool=dict(self.calls_by_tool),
            success_rate=rate,
        )

    def merge_db_metrics(self, db_snapshot: dict) -> ToolMetricsSnapshot:
        local = self.snapshot()
        db_total = db_snapshot.get("total_executions", 0)
        combined_total = local.total_executions + db_total
        db_avg = db_snapshot.get("average_latency_ms", 0.0)
        combined_avg = (
            (local.average_latency_ms * local.total_executions + db_avg * db_total) / combined_total
            if combined_total
            else 0.0
        )
        calls = dict(db_snapshot.get("calls_by_tool", {}))
        for slug, count in local.calls_by_tool.items():
            calls[slug] = calls.get(slug, 0) + count
        success = local.success_count + db_snapshot.get("success_count", 0)
        return ToolMetricsSnapshot(
            total_executions=combined_total,
            success_count=success,
            failure_count=local.failure_count + db_snapshot.get("failure_count", 0),
            permission_denied_count=local.permission_denied_count
            + db_snapshot.get("permission_denied_count", 0),
            validation_failure_count=local.validation_failure_count
            + db_snapshot.get("validation_failure_count", 0),
            average_latency_ms=combined_avg,
            cache_hits=local.cache_hits,
            cache_misses=local.cache_misses,
            calls_by_tool=calls,
            success_rate=success / combined_total if combined_total else 0.0,
        )
