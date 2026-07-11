"""Platform-wide request observability metrics (in-process)."""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class PlatformMetrics:
    """Thread-safe in-process metrics for operational visibility."""

    request_count: int = 0
    error_count: int = 0
    timeout_count: int = 0
    rate_limit_count: int = 0
    exception_counts: dict[str, int] = field(default_factory=dict)
    dependency_failures: dict[str, int] = field(default_factory=dict)
    _latencies_ms: deque = field(default_factory=lambda: deque(maxlen=2000))
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record_request(self, *, latency_ms: float, status_code: int, exception_type: str | None = None) -> None:
        with self._lock:
            self.request_count += 1
            self._latencies_ms.append(latency_ms)
            if status_code >= 400:
                self.error_count += 1
            if exception_type:
                self.exception_counts[exception_type] = self.exception_counts.get(exception_type, 0) + 1

    def record_timeout(self) -> None:
        with self._lock:
            self.timeout_count += 1
            self.error_count += 1
            self.exception_counts["RequestTimeout"] = self.exception_counts.get("RequestTimeout", 0) + 1

    def record_rate_limit(self) -> None:
        with self._lock:
            self.rate_limit_count += 1
            self.error_count += 1
            self.exception_counts["RateLimitExceeded"] = self.exception_counts.get("RateLimitExceeded", 0) + 1

    def record_dependency_failure(self, name: str) -> None:
        with self._lock:
            self.dependency_failures[name] = self.dependency_failures.get(name, 0) + 1

    def _percentile(self, p: float) -> float:
        with self._lock:
            if not self._latencies_ms:
                return 0.0
            sorted_vals = sorted(self._latencies_ms)
            idx = max(0, min(len(sorted_vals) - 1, math.ceil(p / 100.0 * len(sorted_vals)) - 1))
            return round(sorted_vals[idx], 2)

    def snapshot(self) -> dict:
        with self._lock:
            latencies = list(self._latencies_ms)
        avg = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "timeout_count": self.timeout_count,
            "rate_limit_count": self.rate_limit_count,
            "latency_avg_ms": avg,
            "latency_p95_ms": self._percentile(95),
            "latency_p99_ms": self._percentile(99),
            "exception_counts": dict(self.exception_counts),
            "dependency_failures": dict(self.dependency_failures),
            "collected_at": time.time(),
        }


platform_metrics = PlatformMetrics()
