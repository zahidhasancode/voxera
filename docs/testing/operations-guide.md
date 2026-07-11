# Testing Operations Guide

## CI/CD pipeline

GitHub Actions workflow `.github/workflows/ci.yml`:

1. **lint-python** — ruff, black
2. **test-python-unit** — fast unit tests
3. **test-python-integration** — Postgres + migrations + integration
4. **test-python-security** — security marker
5. **test-python-benchmark** — performance smoke
6. **lint-dashboard** — build + Vitest
7. **security-scan** — pip-audit, Trivy
8. **infra-validation** — compose, helm, infra tests

## Load testing (manual)

Requires [k6](https://k6.io/):

```bash
# Health/metrics load
k6 run tests/load/k6-api-load.js -e VOXERA_BASE_URL=https://staging.example.com

# Concurrent voice monitoring profile
k6 run tests/load/k6-voice-concurrent.js -e VOXERA_LOAD_PROFILE=100
```

Profiles: `smoke`, `100`, `500`, `1000`.

## Pre-release checklist

- [ ] `./scripts/run-qa-suite.sh full` passes
- [ ] Coverage ≥ current gate (65%, target 90%)
- [ ] Golden dataset intent accuracy ≥ 90%
- [ ] k6 smoke profile passes
- [ ] No CRITICAL/HIGH Trivy findings unmitigated
- [ ] Staging soak test 24h

## Observability during tests

- Prometheus metrics: `GET /api/v1/metrics`
- Coverage: `reports/coverage/html/index.html`
- Golden eval: pytest output + `EvaluationReport.to_dict()`

## Incident correlation

When production issues occur, replay against:

1. Golden dataset case closest to failure utterance
2. Matching voice simulation scenario
3. Relevant chaos test case

## Contacts

See `docs/operations/incident-response.md` for escalation paths.
