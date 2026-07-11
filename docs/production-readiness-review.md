# VOXERA Production Readiness Engineering Report

> **Superseded for RC1.** Use [docs/release/RC1-production-readiness-report.md](release/RC1-production-readiness-report.md) as the current source of truth (July 2026). This document reflects an earlier read-only audit before RC1 hardening.

**Review type:** Staff-level production readiness audit (read-only)  
**Scope:** Entire repository — backend, voice pipeline, enterprise domains, IAM, dashboard, web, infra, tests, docs  
**Method:** Codebase exploration, architecture review, test inventory, security boundary analysis  
**Constraint:** No code modified; findings based on what exists today  
**Date:** July 11, 2026

---

## Executive Summary

VOXERA is an **ambitious, well-documented enterprise voice platform scaffold** with a **credible domain architecture** for memory, RAG, planner, verifier, workflow, tools, and IAM. The voice pipeline has a **real streaming design** (turn-taking, barge-in, dispatcher, metrics), and enterprise modules follow **ports-and-adapters** patterns with solid unit test coverage for core engines.

However, the project is **not production-ready** and is **not safe to expose to enterprise customers in its current form**. The gap is not primarily "missing features" — it is **missing enforcement at the system boundary**:

- **No HTTP authentication** on enterprise APIs despite IAM existing
- **JWT issued but never validated** on subsequent requests
- **Knowledge/RAG providers are stubs** even when configured
- **Voice stack uses Mock STT/LLM/TTS** in live paths
- **Dashboard is mock-driven**; IAM API client exists but is unused
- **No CI/CD**, incomplete Docker, broken healthcheck pattern
- **Middleware bug** can mask real errors on failed requests

The codebase reads like **multiple strong sprint deliverables** (domain models, migrations, docs, unit tests) assembled **without a production hardening phase**. That is a common and recoverable pattern — but only if the next phase is **security, integration, and ops**, not more surface area.

---

## Scores (0–10)

| Dimension | Score | Rationale |
|-----------|------:|-----------|
| **Architecture** | **6.5** | Strong enterprise domain layering; dual legacy+enterprise stacks; DI god-module; boundary auth missing |
| **Code Quality** | **6.0** | Readable enterprise modules; uneven conventions; dead routes; stubs presented as complete |
| **Security** | **2.5** | Open multi-tenant APIs; spoofable IAM headers; default SECRET_KEY; no Twilio signature validation |
| **Scalability** | **5.0** | Async-first design intent; in-process background jobs; per-worker caches; IAM index drift |
| **Maintainability** | **6.0** | Excellent architecture docs; confusing dual tool services; mock/real split undocumented in ops |
| **Production Readiness** | **3.0** | Cannot safely deploy for enterprise tenants today |

**Overall weighted assessment: ~4.8 / 10** for production readiness.

---

## Strengths

1. **Enterprise domain modeling is serious** — planner, verifier, workflow, tools, memory, RAG, IAM each have schemas, repositories, services, migrations, and architecture docs.
2. **Unit test coverage for engines is meaningful** — ~45 test files covering RBAC, workflow rules, verifier pipeline, planner reasoning, tool circuit breakers, memory compression.
3. **Multi-tenant data model is consistent** — `TenantScopedMixin`, repository filtering, domain-level cross-tenant validators in memory/RAG/tools/planner/verifier/workflow.
4. **Voice pipeline architecture is sound on paper** — `AudioFrameQueue`, `StreamingDispatcher`, `TurnManager`, barge-in cancellation, streaming metrics.
5. **Tool framework is production-shaped** — validation, permissions, retry, circuit breaker, audit trail.
6. **IAM foundation is real** — bcrypt passwords, JWT issuance, HMAC API keys, RBAC catalog, immutable audit schema (not just "login page").
7. **Documentation quality is above average** for an early-stage platform — 14 architecture docs including state/sequence diagrams.
8. **Dashboard UX direction is enterprise-grade** — component system, lazy routes, accessibility primitives, operations console layout.

---

## Weaknesses

1. **Security boundary is effectively open** — biggest single failure mode.
2. **Implementation vs documentation mismatch** — many subsystems documented as complete are stubbed or mock-backed.
3. **Two parallel architectures** — legacy `app/services/` + `app/models/` vs enterprise `app/infrastructure/` without a hard boundary.
4. **No automated quality gates** — no CI, no migration tests, no API integration tests.
5. **Frontend not connected to backend** — dashboard and web largely demo/mock despite backend APIs existing.
6. **Operational story incomplete** — Docker, health checks, observability, secrets management not production-grade.

---

# Critical Issues

### CR-01 — Enterprise REST APIs are unauthenticated

| Field | Detail |
|-------|--------|
| **Priority** | Critical |
| **Location** | `app/api/v1/endpoints/*`, `app/memory/api/routes.py`, `app/planner/api/routes.py`, `app/knowledge/api/routes.py`, etc. |
| **Problem** | Any caller can invoke `/api/v1/tenants/{tenant_id}/...` with arbitrary UUIDs. No `Depends(get_current_user)` or Bearer validation anywhere in HTTP layer. |
| **Why it matters** | Complete tenant data exposure and mutation. Enterprise isolation is path-parameter security, not identity security. |
| **Enterprise impact** | Immediate compliance failure (SOC2, GDPR access control). Unacceptable for any paid tenant. |
| **Recommended solution** | JWT + API key middleware; protect all `/api/v1/tenants/*` and `/api/v1/iam/*` (except login/register). Bind caller identity to tenant membership. |
| **Complexity** | Medium |
| **Effort** | 1–2 weeks |

---

### CR-02 — IAM validates nothing at the HTTP boundary

| Field | Detail |
|-------|--------|
| **Priority** | Critical |
| **Location** | `app/iam/api/routes.py`, `app/iam/auth/token_service.py` |
| **Problem** | Login returns JWT; `decode_token()` is never used by routes. Privileged IAM actions use spoofable `X-Actor-Id` header. Many IAM endpoints have no auth at all. |
| **Why it matters** | IAM gives false confidence. RBAC exists in code but not in request path. |
| **Enterprise impact** | Any client can impersonate any user UUID and perform admin actions if they know org IDs. |
| **Recommended solution** | `get_current_user` FastAPI dependency; replace `X-Actor-Id` with JWT claims; wire `authenticate_api_key` for machine clients. |
| **Complexity** | Medium |
| **Effort** | 1 week (after CR-01 foundation) |

---

### CR-03 — Knowledge embedding/vector providers are stubs

| Field | Detail |
|-------|--------|
| **Priority** | Critical |
| **Location** | `app/infrastructure/knowledge/providers.py` |
| **Problem** | When `KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER` / `KNOWLEDGE_DEFAULT_VECTOR_STORE` are set, code returns `UnconfiguredEmbeddingProvider` / `UnconfiguredVectorStore` — not real implementations. |
| **Why it matters** | Knowledge ingestion and RAG cannot work in production regardless of env configuration. |
| **Enterprise impact** | Core product promise (enterprise KB + RAG) is non-functional end-to-end. |
| **Recommended solution** | Implement at least one real provider pair (e.g. pgvector + OpenAI embeddings, or Pinecone). Fail fast at startup if misconfigured. |
| **Complexity** | High |
| **Effort** | 2–3 weeks |

---

### CR-04 — Background ingestion uses request-scoped DB session in detached tasks

| Field | Detail |
|-------|--------|
| **Priority** | Critical |
| **Location** | `app/infrastructure/knowledge/background_processor.py`, `app/api/v1/dependencies.py` |
| **Problem** | `asyncio.create_task` runs ingestion after HTTP response; uses session from request DI lifecycle. |
| **Why it matters** | Race conditions, closed sessions, silent ingestion failures under load. |
| **Enterprise impact** | Unreliable document indexing — data loss perception for customers. |
| **Recommended solution** | Worker queue (Celery/ARQ/SQS) with dedicated session per job; or `session_scope()` inside task with explicit lifecycle. |
| **Complexity** | Medium–High |
| **Effort** | 1–2 weeks |

---

### CR-05 — Default SECRET_KEY ships in config

| Field | Detail |
|-------|--------|
| **Priority** | Critical |
| **Location** | `app/core/config.py`, `.env.example` |
| **Problem** | Default `"change-this-secret-key-in-production-use-env-vars-min-32-chars"` used for JWT, API key HMAC, and field encryption. |
| **Why it matters** | Predictable token forgery if deployed without override. |
| **Enterprise impact** | Total auth compromise in misconfigured deployments. |
| **Recommended solution** | Fail startup in production if SECRET_KEY is default; separate keys for JWT vs API keys vs encryption. |
| **Complexity** | Low |
| **Effort** | 1–2 days |

---

### CR-06 — Request middleware masks exceptions

| Field | Detail |
|-------|--------|
| **Priority** | Critical |
| **Location** | `app/core/middleware.py` lines 40–62 |
| **Problem** | On exception, `response` is never assigned, but `finally` accesses `response.headers` → potential `UnboundLocalError` masking original error. |
| **Why it matters** | Debugging production incidents becomes harder; secondary failures hide root cause. |
| **Enterprise impact** | Extended MTTR, unreliable error surfaces for SRE. |
| **Recommended solution** | Initialize `response = None`; guard `finally` block; add global exception handler in `main.py`. |
| **Complexity** | Low |
| **Effort** | 2–4 hours |

---

### CR-07 — Voice pipeline uses Mock engines in production paths

| Field | Detail |
|-------|--------|
| **Priority** | Critical (for voice product) |
| **Location** | `app/api/v1/endpoints/websocket.py`, `app/telephony/call_session.py` |
| **Problem** | `MockSTTEngine`, `MockStreamingLLMEngine`, `MockStreamingTTSEngine` wired in live WebSocket and Twilio paths. |
| **Why it matters** | Voice is the core product; mocks are fine for dev, not for enterprise delivery. |
| **Enterprise impact** | Product does not deliver real voice AI in production. |
| **Recommended solution** | Provider abstraction exists — wire real STT/LLM/TTS with config-driven selection; keep mocks for test only. |
| **Complexity** | High |
| **Effort** | 3–6 weeks (provider-dependent) |

---

### CR-08 — No CI/CD pipeline

| Field | Detail |
|-------|--------|
| **Priority** | Critical |
| **Location** | Repository root — no `.github/workflows/` |
| **Problem** | No automated pytest, lint, build, migration validation, or security scanning on every change. |
| **Why it matters** | Regressions ship silently; team velocity creates debt faster than it is detected. |
| **Enterprise impact** | Cannot certify release quality to enterprise buyers. |
| **Recommended solution** | GitHub Actions: pytest, ruff, mypy, alembic check, dashboard/web build, Docker build. |
| **Complexity** | Low–Medium |
| **Effort** | 3–5 days |

---

# High Priority Improvements

### HI-01 — Twilio webhook has no signature validation

| | |
|--|--|
| **Location** | `app/telephony/twilio_handler.py` |
| **Problem** | No `X-Twilio-Signature` verification; no `TWILIO_AUTH_TOKEN` in config |
| **Impact** | Spoofed inbound calls, media stream hijacking |
| **Solution** | Twilio request validator middleware |
| **Effort** | 2–3 days |

### HI-02 — WebSocket connections unauthenticated

| | |
|--|--|
| **Location** | `app/core/connection_manager.py`, `app/api/v1/endpoints/websocket.py` |
| **Problem** | Comment says auth will be added; none exists |
| **Impact** | Open real-time voice/control plane |
| **Solution** | Token query param or subprotocol auth; tenant/agent binding |
| **Effort** | 1 week |

### HI-03 — IAM migration index drift

| | |
|--|--|
| **Location** | `alembic/versions/008_enterprise_iam_schema.py` vs `app/database/models/iam.py` |
| **Problem** | Migration creates ~1 index; ORM declares indexes on email, token_hash, audit timestamps, FKs |
| **Impact** | IAM queries degrade at scale; autogenerate drift risk |
| **Solution** | Migration 009 to add missing indexes; composite indexes for audit/hot paths |
| **Effort** | 2–3 days |

### HI-04 — Health check does not verify dependencies

| | |
|--|--|
| **Location** | `app/api/v1/endpoints/health.py` |
| **Problem** | Always returns `"healthy"`; no DB ping, no provider readiness |
| **Impact** | Orchestrator routes traffic to broken instances |
| **Solution** | `/health/live` + `/health/ready` with DB check |
| **Effort** | 1–2 days |

### HI-05 — Docker production image incomplete

| | |
|--|--|
| **Location** | `Dockerfile`, `docker-compose.yml` |
| **Problem** | No Alembic in image; healthcheck uses `curl` (not installed); no Postgres; single uvicorn worker |
| **Impact** | Broken deploy story |
| **Solution** | Multi-stage build, healthcheck via Python, compose with Postgres, migration init |
| **Effort** | 3–5 days |

### HI-06 — Dashboard disconnected from backend

| | |
|--|--|
| **Location** | `dashboard/src/contexts/*`, `dashboard/src/lib/iam.ts` |
| **Problem** | IAM API client exists but unused; all contexts mock; operations WS URL documented but **no backend route** |
| **Impact** | Admin console is a prototype, not an operating system |
| **Solution** | Wire auth → IAM login; replace mocks incrementally; implement or remove `/ws/operations` |
| **Effort** | 2–4 weeks |

### HI-07 — Blocking I/O in async paths

| | |
|--|--|
| **Location** | `app/infrastructure/knowledge/storage.py`, `plain_text_parser.py` |
| **Problem** | Sync filesystem reads/writes in `async def` |
| **Impact** | Event loop blocking under ingestion load |
| **Solution** | `asyncio.to_thread()` or aiofiles |
| **Effort** | 2–3 days |

### HI-08 — Inconsistent error handling on REST writes

| | |
|--|--|
| **Location** | `app/api/v1/endpoints/agents.py`, `tenants.py`, `knowledge/api/routes.py` |
| **Problem** | Some routes use `map_domain_errors`; create/list often don't; SQLAlchemy `IntegrityError` unmapped |
| **Impact** | 500 instead of 409/422; poor API contract |
| **Solution** | Global exception handlers + consistent route wrapper |
| **Effort** | 3–5 days |

### HI-09 — RAG ranking strategies mostly unimplemented

| | |
|--|--|
| **Location** | `app/rag/ranking/strategies.py` |
| **Problem** | 5 of 6 strategies raise `NotImplementedError` at runtime |
| **Impact** | Runtime failures if configured; false completeness |
| **Solution** | Implement or remove from registry; document supported strategies only |
| **Effort** | 1–2 weeks |

### HI-10 — No HTTP rate limiting

| | |
|--|--|
| **Location** | Platform-wide |
| **Problem** | Tool-level rate limits only; no global/API gateway limits |
| **Impact** | Abuse, cost explosion on LLM/STT/TTS |
| **Solution** | Middleware or API gateway rate limits; enforce IAM policy `rate_limits` |
| **Effort** | 1 week |

---

# Medium Priority Improvements

| ID | Location | Problem | Effort |
|----|----------|---------|--------|
| M-01 | `app/api/v1/dependencies.py` | God-module DI (~300 lines, 30+ imports) | 1 week refactor |
| M-02 | `app/api/v1/endpoints/audio.py` | ~429 lines, unmounted dead router | 1 day delete or wire |
| M-03 | `app/workflow/services/workflow_service.py` | Unused infra import (layer violation smell) | 1 hour |
| M-04 | Dual tool services naming | `tools/service.py` vs tool execution routes confusion | 2 days rename/docs |
| M-05 | `web/src/components/MicPanel.tsx` | No binary PCM upload despite README claims | 1 week |
| M-06 | `@lru_cache` singletons | Not shared across workers; stale config risk | 3 days |
| M-07 | `LocalSecretProvider` | XOR encryption, not AEAD; single SECRET_KEY | 1 week |
| M-08 | Missing composite DB indexes | `(tenant_id, conversation_id)`, turn ordering | 3 days |
| M-09 | No integration tests for REST | Zero TestClient coverage | 2 weeks |
| M-10 | pyproject.toml vs requirements.txt drift | PyJWT/bcrypt missing from Poetry | 1 day |
| M-11 | Permissive CORS | `allow_methods/headers=["*"]` in production config path | 1 day |
| M-12 | PDF/DOCX parsers | `UnsupportedDocumentParser` for most formats | 2–3 weeks |

---

# Low Priority Improvements

| ID | Location | Problem | Effort |
|----|----------|---------|--------|
| L-01 | `app/utils/` | Empty vestigial package | 1 hour |
| L-02 | `datetime.utcnow()` | Deprecated in health endpoint | 1 hour |
| L-03 | Dashboard test coverage | 3 Vitest files only | Ongoing |
| L-04 | web/ has no tests | Zero frontend tests for voice client | 1 week |
| L-05 | OpenAPI disabled in prod | Fine, but no external API catalog | 2 days |
| L-06 | Inconsistent domain folder depth | tenants vs knowledge module structure | Ongoing convention |
| L-07 | Magic link IAM endpoint | Stub returns "sent" | When SSO roadmap clear |

---

# Section Reviews (Summary)

### 1. Folder Structure — 6/10

Scalable for enterprise domains. **Risk:** legacy `services/` + `models/` parallel to `infrastructure/` creates onboarding confusion. Dead `audio.py`, empty `utils/`.

### 2. Architecture — 6.5/10

Clean separation in enterprise modules (domain ports → infra repos). **Violations:** composition root knows all concrete classes; workflow unused infra import; ranking strategies registered but unimplemented.

### 3. Code Quality — 6/10

Enterprise modules are readable with consistent schemas. **Issues:** stubs documented as features, magic defaults, large `dependencies.py`, dead code.

### 4. Streaming Voice Pipeline — 5/10 design, 2/10 production

Good turn-taking and dispatcher design. **Production gap:** mock engines, no WS auth, Twilio unsigned, web client doesn't stream mic PCM, legacy `audio.py` orphaned.

### 5. Memory System — 7/10

Solid design with compression, summarizer, working memory, access validators. **Gaps:** no integration tests with Postgres; cleanup/TTL policies not verified at scale.

### 6. RAG — 5/10

Good context builder and tenant isolation validators. **Gaps:** stub vector/embedding providers; most ranking strategies unimplemented; no end-to-end retrieval test against real index.

### 7. Planner — 7/10

Reasonable reasoning loop, policy engine, context optimizer. **Gaps:** no integration with live LLM; context size limits not load-tested.

### 8. Verifier — 7.5/10

Strongest enterprise module — pipeline, compliance, risk engine, good unit tests. **Gap:** still operates on structured/mock model path, not live planner output in production.

### 9. Workflow Engine — 6.5/10

Configurable rules, approvals, escalation, event bus — well tested. **Gaps:** distributed workers not implemented; approval/escalation persistence partially wired; not integrated into live call flow.

### 10. Tool Registry — 7/10

Plugin architecture, circuit breaker, retry, audit — production-shaped. **Gap:** HTTP tool guardrails need security review for SSRF in production.

### 11. Security — 2.5/10

See Critical Issues. Domain isolation exists; **HTTP boundary does not.**

### 12. Database — 6/10

8 migrations, 47 models, reasonable relationships. **Gaps:** IAM index drift, missing composite indexes for conversation/history queries, no migration test CI.

### 13. Frontend — 5/10 UX, 2/10 integration

Dashboard looks enterprise-grade. **Almost entirely mock.** web/ has real WS for dev triggers but not full voice ingest.

### 14. API Design — 6/10

Consistent `/api/v1/tenants/{tid}/agents/{aid}/...` pattern. **Gaps:** no pagination standard on all list endpoints, inconsistent error envelopes, no auth.

### 15. Performance — 5/10

Async-first intent; streaming metrics exist. **Risks:** blocking file I/O, in-process background jobs, no load tests, per-worker caches.

### 16. Observability — 4/10

Structured logging with request IDs. **Missing:** distributed tracing, metrics export (Prometheus), alerting runbooks, correlated audit across services.

### 17. Testing — 5.5/10

~45 unit test files — good for engines. **Missing:** integration, E2E, load, voice pipeline, REST API, migration, IAM HTTP tests.

### 18. Documentation — 7.5/10

Excellent architecture docs for enterprise modules. **Missing:** deployment runbook, CI/CD, observability, telephony ops, API reference beyond FastAPI /docs.

### 19. Deployment — 2.5/10

Dockerfile exists but incomplete. Compose has no database. No CI. Healthcheck broken pattern.

### 20. Technical Debt Register

| Rank | Item | Priority |
|------|------|----------|
| 1 | Open enterprise APIs | Critical |
| 2 | IAM auth not enforced | Critical |
| 3 | Stub knowledge providers | Critical |
| 4 | Mock voice engines in prod path | Critical |
| 5 | Background job session lifecycle | Critical |
| 6 | No CI/CD | Critical |
| 7 | Dashboard mock vs real API | High |
| 8 | Docker/compose incomplete | High |
| 9 | Twilio/WS auth missing | High |
| 10 | IAM migration index drift | High |
| 11 | Middleware exception bug | Critical |
| 12 | Dual architecture (legacy + enterprise) | Medium |
| 13 | Dead audio.py router | Medium |
| 14 | RAG unimplemented strategies | Medium |
| 15 | No HTTP rate limiting | High |
| 16 | Blocking I/O in async | Medium |
| 17 | Operations WS documented but missing | High |
| 18 | Default SECRET_KEY | Critical |
| 19 | No integration/load tests | High |
| 20 | pyproject/requirements drift | Low |

---

# Suggested Refactoring (No New Features)

1. **Hardening sprint** before any new domain modules: auth middleware, exception handlers, middleware fix, SECRET_KEY guard.
2. **Collapse dual architecture boundary** — document and deprecate legacy `app/services/` path; single voice entry via `websocket.py` + Twilio.
3. **Split `dependencies.py`** into domain-specific dependency modules.
4. **Provider registry pattern** — startup validation that configured providers are real, not `Unconfigured*`.
5. **Wire dashboard to IAM** — one vertical slice (login → org → users → API keys) before expanding mocks.

---

# Future Risks

| Risk | Likelihood | Impact |
|------|------------|--------|
| Shipping "complete" modules that are stub-backed | High | Customer churn, security audit failure |
| Continued feature expansion without auth | High | Expensive rework, breach |
| IAM index drift causing prod incidents at scale | Medium | High |
| In-process background jobs under multi-worker deploy | High | Data corruption / lost jobs |
| False demo → sales → failed POC | High | Reputation damage |
| Dual codebase confusion for new engineers | Medium | Velocity loss |

---

# Production Readiness Checklist

| Gate | Status |
|------|--------|
| Authentication on all enterprise routes | ❌ |
| Authorization (RBAC) enforced at HTTP layer | ❌ |
| API key auth wired | ❌ |
| Secrets rotated; no default SECRET_KEY in prod | ❌ |
| Real STT/LLM/TTS providers | ❌ |
| Real embedding/vector store | ❌ |
| Knowledge ingestion reliable (worker queue) | ❌ |
| Twilio signature validation | ❌ |
| WebSocket authentication | ❌ |
| CI/CD (test + lint + build) | ❌ |
| Docker deploy with DB + migrations | ❌ |
| Health ready/live with dependency checks | ❌ |
| IAM DB indexes match queries | ❌ |
| Dashboard wired to IAM/API | ❌ |
| Integration tests (REST + DB) | ❌ |
| Load tests (WS + API) | ❌ |
| Global exception handling | ❌ |
| Rate limiting | ❌ |
| Observability (metrics/tracing) | ❌ |
| Deployment runbook | ❌ |
| Domain unit tests for engines | ✅ |
| Architecture documentation | ✅ |
| Multi-tenant repository isolation | ✅ (data layer) |
| Alembic migrations exist | ✅ |

**Checklist pass rate: ~4/22 (~18%)**

---

# Overall Recommendation

**Stop adding enterprise surface area.** The platform has sufficient module breadth for a first enterprise POC **on paper**. The next phase must be **production hardening and integration**, treated as a release gate, not a parallel workstream.

**Recommended sequence:**

1. CI/CD + middleware fix + global exception handling (week 1)
2. JWT/API key auth on all routes (weeks 1–2)
3. Real knowledge providers + background worker (weeks 2–4)
4. Docker/compose/health/migrations (week 2)
5. Wire dashboard auth + one admin vertical (weeks 3–5)
6. Real voice providers + Twilio auth (weeks 4–8)
7. Integration + load tests (ongoing from week 3)

---

# Final Answer

## Can VOXERA safely continue toward enterprise production?

### No — not safely, on the current trajectory.

You **can** continue engineering toward enterprise production, but **only if the next work is remediation and integration, not new modules**. Continuing to expand features while HTTP security is open, providers are stubbed, the dashboard is mock-driven, and CI/CD is absent is **unsafe** — it increases the gap between perceived completeness and operational reality.

### What must be completed before onboarding the first enterprise customer

1. **Enforce authentication and authorization** on every enterprise and IAM route (JWT + API keys + RBAC).
2. **Remove default SECRET_KEY** and fail closed in production configuration.
3. **Fix middleware exception handling** and add global error handlers.
4. **Ship real knowledge/RAG providers** end-to-end (embed → index → retrieve) with reliable background ingestion.
5. **Wire real STT/LLM/TTS providers** for the voice path (or explicitly scope first customer to non-voice API-only if voice is deferred).
6. **Validate Twilio webhooks** and authenticate WebSockets.
7. **CI/CD** running pytest, lint, build, and migration checks on every merge.
8. **Production deploy stack**: Postgres, migrations, working healthchecks, secrets management.
9. **Connect dashboard** to IAM/API for admin operations (not mock contexts).
10. **Integration tests** proving tenant isolation with authenticated callers — not just repository unit tests.
11. **IAM database indexes** aligned with migrations.
12. **Rate limiting** and basic abuse protection on public endpoints.

Until those gates are met, VOXERA is a **strong architecture and POC codebase**, not an **enterprise production platform**. The foundation is worth continuing — but the next mile is hardening, not breadth.
