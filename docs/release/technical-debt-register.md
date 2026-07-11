# Technical Debt Register — RC1

| ID | Debt | Priority | Effort | Target |
|----|------|----------|--------|--------|
| TD-01 | Dual voice stacks (`app/services/` vs `app/voice/`) | P1 | Large | v1.1 |
| TD-02 | `app/core/enums.py` monolith (762 lines) | P2 | Medium | v1.1 |
| TD-03 | `dependencies.py` god-module wiring | P2 | Medium | v1.1 |
| TD-04 | 186 `NotImplementedError` ABC stubs — verify all wired | P2 | Medium | GA |
| TD-05 | Hand-rolled Prometheus metrics vs prometheus-client | P3 | Small | v1.1 |
| TD-06 | Domain metrics not exported to `/metrics` | P2 | Medium | GA |
| TD-07 | Dashboard: 1 Vitest file, web: 0 tests | P2 | Medium | GA |
| TD-08 | Deploy workflows echo-only (no kube deploy) | P2 | Medium | GA |
| TD-09 | Integration providers: catalog without live fetchers | P1 | Large | v1.1 |
| TD-10 | Empty `app/utils/` module | P3 | Trivial | v1.1 |
| TD-11 | Root orphan `test_streaming.py` | P3 | Trivial | v1.1 |
| TD-12 | Six overlapping audit service modules | P3 | Medium | v2.0 |
| TD-13 | Duplicate CallSession types | P2 | Medium | v1.1 |
| TD-14 | Alertmanager not configured | P2 | Small | GA |
| TD-15 | Stale product docs (`production-readiness-review.md`) | P3 | Small | RC1 ✓ |
