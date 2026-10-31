"""Performance smoke tests against SLO targets."""

from __future__ import annotations

import pytest

from tests.utilities.benchmarks import BenchmarkReport, SLO, measure_latency


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_health_live_latency_slo(http_client):
    report = BenchmarkReport()
    for _ in range(10):
        with measure_latency(report, "health_live"):
            response = await http_client.get("/api/v1/health/live")
        assert response.status_code == 200
    assert report.p95("health_live") <= SLO["health_live"] * 3
