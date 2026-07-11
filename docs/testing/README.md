# VOXERA Enterprise Testing & Validation

This directory contains the QA strategy, guides, and quality gates for the VOXERA platform.

## Quick start

```bash
# PR-quality gate (unit + security + e2e + benchmarks)
./scripts/run-qa-suite.sh pr

# Full suite including integration, chaos, coverage
./scripts/run-qa-suite.sh full
```

## Test layout

| Directory | Purpose |
|-----------|---------|
| `tests/unit/` (legacy: subsystem dirs) | Fast isolated unit tests |
| `tests/integration/` | API, DB, performance smoke |
| `tests/e2e/` | Golden dataset AI eval, voice simulation |
| `tests/security/` | JWT, tenant isolation, injection |
| `tests/chaos/` | Fault injection, graceful degradation |
| `tests/load/` | k6 load scripts (manual/scheduled) |
| `tests/datasets/golden/` | Versioned evaluation datasets |
| `tests/fixtures/` | Shared pytest fixtures |
| `tests/utilities/` | Voice simulator, benchmarks, evaluation |

## Guides

- [Testing Strategy](./testing-strategy.md)
- [QA Guide](./qa-guide.md)
- [Simulation Guide](./simulation-guide.md)
- [Benchmark Guide](./benchmark-guide.md)
- [Chaos Engineering Guide](./chaos-engineering-guide.md)
- [Operations Guide](./operations-guide.md)

## Quality gates

| Gate | Threshold | Enforced in |
|------|-----------|-------------|
| Unit tests | All pass | CI `test-python-unit` |
| Integration | All pass (with Postgres) | CI `test-python-integration` |
| Security | All pass | CI `test-python-security` |
| Coverage | ≥65% (ratchet → 90%) | CI coverage job |
| Performance smoke | p95 within SLO×5 | CI benchmark job |
| Load (optional) | k6 thresholds | Scheduled / pre-release |

## Reports

Coverage HTML: `reports/coverage/html/`  
Coverage XML: `reports/coverage/coverage.xml`
