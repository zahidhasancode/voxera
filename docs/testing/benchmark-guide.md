# Benchmark Guide

## SLO targets

Defined in `tests/utilities/benchmarks.py`:

| Metric | SLO (p95 ms) |
|--------|--------------|
| `health_live` | 50 |
| `health_ready` | 500 |
| `planner_intent_classify` | 25 |
| `verifier_pipeline` | 100 |
| `api_metrics` | 100 |

## Smoke tests

`tests/integration/performance/test_latency_smoke.py` runs bounded iterations and asserts p95 ≤ SLO × multiplier (5× in CI for headroom).

## Running benchmarks

```bash
pytest tests/integration/performance/ -m benchmark -v
```

## Production targets (voice)

| Metric | Target |
|--------|--------|
| First transcript latency | < 800 ms |
| First token latency | < 1200 ms |
| First audio latency | < 1500 ms |
| Roundtrip latency | < 2000 ms |
| Retrieval latency | < 300 ms |
| Planner latency | < 500 ms |
| Verifier latency | < 200 ms |

Full voice latency benchmarks require staging with real STT/TTS providers.

## Regression gate

Block deployment if performance smoke p95 regresses >10% vs baseline (future: store baseline in CI artifacts).

## Reporting

`BenchmarkReport` supports `p95`, `avg`, and `max` per metric name for custom report generation.
