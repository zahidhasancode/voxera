# Chaos Engineering Guide

## Scope

Chaos tests validate graceful degradation — not catastrophic failure. They use mocks/fault injection without modifying production code paths.

## Test suite

`tests/chaos/test_graceful_degradation.py`:

| Test | Fault | Expected behavior |
|------|-------|-------------------|
| Database down | Mock `check_database` unhealthy | Readiness degraded/unhealthy |
| Liveness | DB fault during live check | Live remains healthy |
| Circuit breaker | Tool provider failures | Breaker opens after threshold |

## Running

```bash
pytest tests/chaos/ -m chaos -v
```

## Planned extensions

| Fault | Method |
|-------|--------|
| Redis failure | Mock cache layer when Redis enabled |
| Vector DB failure | Mock embedding provider unhealthy |
| Provider timeout | Tool execution timeout injection |
| Twilio disconnect | Telephony mock hangup |
| Worker crash | Process supervisor restart (K8s) |
| Queue overflow | Backpressure metrics assertion |

## Kubernetes chaos

For production-like chaos, use staging cluster tools (e.g. pod kill, network partition) with:

- PodDisruptionBudgets (configured in Helm)
- Readiness/liveness probes
- HPA and circuit breakers

## Recovery criteria

- Liveness endpoint returns 200 within 5s of process start
- Readiness reflects dependency state accurately
- No unbounded error rate after fault removal
- Circuit breaker recovers after `recovery_seconds`
