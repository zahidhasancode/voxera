# VOXERA Testing Strategy

## Mission

Validate every subsystem automatically, every deployment safely, and every AI workflow measurably — without changing product architecture or business logic.

## Test pyramid

```
                    ┌─────────────┐
                    │  Load/Chaos │  (scheduled / pre-release)
                    ├─────────────┤
                    │    E2E      │  Golden datasets, voice sim
                    ├─────────────┤
                    │ Integration │  API, DB, IAM HTTP
                    ├─────────────┤
                    │    Unit     │  Planner, Verifier, Workflow, …
                    └─────────────┘
```

## Subsystem coverage map

| Subsystem | Unit | Integration | E2E | Security |
|-----------|------|-------------|-----|----------|
| Planner | ✓ | smoke | golden intent | — |
| Verifier | ✓ | smoke | golden (planned) | — |
| Workflow | ✓ | — | — | — |
| Tool Registry | ✓ | — | — | permissions |
| Memory | ✓ | — | — | tenant |
| Knowledge/RAG | ✓ | — | — | upload validation |
| IAM | ✓ | API contract | — | JWT, RBAC, tenant |
| Voice | ✓ | — | simulation | stream auth |
| Dashboard | Vitest | — | — | — |
| Infra/Deploy | ✓ | compose/helm | — | scan |

## Markers

Defined in `pytest.ini`:

- `unit` — default, fast, mocked I/O
- `integration` — requires `DATABASE_URL`
- `e2e` — multi-subsystem scenarios
- `voice` — audio/WebSocket paths
- `security` — abuse and auth cases
- `chaos` — fault injection
- `benchmark` — latency SLO smoke
- `slow` — load tests

## Golden dataset evaluation

Versioned JSON under `tests/datasets/golden/` covers healthcare, ecommerce, banking, telecom, insurance, travel, and support.

Metrics tracked per run:

- Intent accuracy
- Tool selection accuracy (when wired)
- Verifier approval accuracy (when wired)
- Hallucination / grounding (via verifier suite)

## Regression policy

Every PR runs:

1. Lint (ruff, black)
2. Unit tests
3. Security tests
4. E2E smoke (golden + voice sim)
5. Performance benchmark smoke
6. Dashboard build + Vitest

Integration and chaos run on merge to `main` / nightly.

## Coverage ratchet

| Phase | Target | Gate |
|-------|--------|------|
| Current | 65% | CI fail-under |
| Next | 80% | raise `fail_under` |
| Production | 90% | deployment gate |

## Non-goals

- No demo/flaky tests
- No production feature changes for testability
- No architecture redesign
