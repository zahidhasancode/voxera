"""Integration platform metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class IntegrationMetricsCollector:
    sync_latencies_ms: list[float] = field(default_factory=list)
    webhook_latencies_ms: list[float] = field(default_factory=list)
    sync_failures: int = 0
    webhook_failures: int = 0
    oauth_refresh_count: int = 0
    _lock: Lock = field(default_factory=Lock)

    def record_sync(self, provider: str, latency_ms: float, *, success: bool) -> None:
        with self._lock:
            if success:
                self.sync_latencies_ms.append(latency_ms)
                if len(self.sync_latencies_ms) > 1000:
                    self.sync_latencies_ms = self.sync_latencies_ms[-500:]
            else:
                self.sync_failures += 1

    def record_webhook(self, provider: str, latency_ms: float, *, success: bool) -> None:
        with self._lock:
            if success:
                self.webhook_latencies_ms.append(latency_ms)
                if len(self.webhook_latencies_ms) > 1000:
                    self.webhook_latencies_ms = self.webhook_latencies_ms[-500:]
            else:
                self.webhook_failures += 1

    def record_oauth_refresh(self) -> None:
        with self._lock:
            self.oauth_refresh_count += 1

    def snapshot(self) -> dict[str, float | int]:
        with self._lock:
            avg_sync = (
                sum(self.sync_latencies_ms) / len(self.sync_latencies_ms)
                if self.sync_latencies_ms
                else 0.0
            )
            avg_webhook = (
                sum(self.webhook_latencies_ms) / len(self.webhook_latencies_ms)
                if self.webhook_latencies_ms
                else 0.0
            )
            return {
                "avg_sync_latency_ms": round(avg_sync, 2),
                "avg_webhook_latency_ms": round(avg_webhook, 2),
                "sync_failures": self.sync_failures,
                "webhook_failures": self.webhook_failures,
                "oauth_refresh_count": self.oauth_refresh_count,
            }


integration_metrics = IntegrationMetricsCollector()
