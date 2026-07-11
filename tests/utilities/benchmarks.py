"""Performance benchmark helpers."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class LatencySample:
    name: str
    duration_ms: float


@dataclass
class BenchmarkReport:
    samples: list[LatencySample] = field(default_factory=list)

    def add(self, name: str, duration_ms: float) -> None:
        self.samples.append(LatencySample(name=name, duration_ms=duration_ms))

    def p95(self, name: str | None = None) -> float:
        values = [
            s.duration_ms
            for s in self.samples
            if name is None or s.name == name
        ]
        if not values:
            return 0.0
        values.sort()
        idx = max(0, int(len(values) * 0.95) - 1)
        return values[idx]

    def max(self, name: str | None = None) -> float:
        values = [s.duration_ms for s in self.samples if name is None or s.name == name]
        return max(values) if values else 0.0

    def avg(self, name: str | None = None) -> float:
        values = [s.duration_ms for s in self.samples if name is None or s.name == name]
        return sum(values) / len(values) if values else 0.0


@contextmanager
def measure_latency(report: BenchmarkReport, name: str) -> Iterator[None]:
    start = time.perf_counter()
    yield
    report.add(name, (time.perf_counter() - start) * 1000.0)


# SLO targets (milliseconds) — used by smoke tests
SLO = {
    "health_live": 50.0,
    "health_ready": 500.0,
    "planner_intent_classify": 25.0,
    "verifier_pipeline": 100.0,
    "api_metrics": 100.0,
}
