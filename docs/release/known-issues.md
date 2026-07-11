# VOXERA v1.0.0-RC1 — Known Issues

| ID | Severity | Area | Description | Workaround |
|----|----------|------|-------------|------------|
| RC1-001 | High | Security | Per-route RBAC not enforced on tenant REST endpoints | Restrict network access; use dedicated service accounts |
| RC1-002 | High | Voice | Twilio STT bridge uses MockSTTEngine when provider not configured | Configure real STT provider; use main WebSocket path for demos |
| RC1-003 | High | Observability | No application OpenTelemetry instrumentation | Use structured logs + Prometheus metrics |
| RC1-004 | Medium | Rate limits | In-process only; ineffective multi-pod without Redis | Single replica or accept per-pod limits |
| RC1-005 | Medium | Dashboard | Live Calls empty — operations WebSocket not implemented | Use metrics endpoint + call detail pages |
| RC1-006 | Medium | Dashboard | Billing/Analytics backends not wired | Empty states shown |
| RC1-007 | Medium | CI | Security scans do not fail build on CRITICAL/HIGH | Manual Trivy/pip-audit review before deploy |
| RC1-008 | Medium | Metrics | `/api/v1/metrics` publicly accessible | NetworkPolicy + ingress restriction |
| RC1-009 | Low | Tests | Coverage gate 65% (target 90%) | Prioritize API integration tests |
| RC1-010 | Low | Tests | WebSocket e2e skipped when httpx ≠ 0.26.0 | Pin httpx in dev environments |
| RC1-011 | Low | Docs | Stale `production-readiness-review.md` | Use `docs/release/` as source of truth |
| RC1-012 | Low | Integrations | Provider sync returns empty until live fetchers implemented | Manual data import; webhook ingestion |

## Deferred to GA

- Redis health check and rate limit backing
- Cloud secret providers (AWS/Azure/GCP/Vault)
- Image signing (cosign)
- Automated Helm deploy in CI
