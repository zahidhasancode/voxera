# Sprint 1 — Enterprise Multi-Tenant Architecture

This document describes the **Sprint 1** extension to VOXERA: a production-oriented multi-tenant layer added **alongside** the existing real-time voice pipeline. The streaming path (Twilio Media Streams, WebSocket STT/LLM/TTS, latency optimizations) is **unchanged**.

## Design Principles

| Layer | Responsibility |
|-------|----------------|
| **Domain** (`app/tenants`, `app/agents`, …) | Pydantic schemas, repository ports (ABC), service ports (ABC) |
| **Infrastructure** (`app/infrastructure`) | SQLAlchemy repository adapters, thin service implementations |
| **Database** (`app/database`) | ORM models, async session, Alembic migrations |
| **API** (`app/api/v1`) | Thin REST endpoints — delegate to services only |
| **Core** (`app/core`) | Config, enums, shared schemas, exceptions |

**No business logic in endpoints.** Validation rules, authorization, audit side-effects, and voice-runtime integration land in Sprint 2+.

## Domain Model

```
Tenant (root)
 ├── Agent (1:N)
 │    └── AgentConfiguration (1:1)
 ├── KnowledgeBase (1:N)
 ├── Tool (1:N)
 └── AuditLog (1:N, append-only)
```

Every tenant-scoped resource carries `tenant_id` for row-level isolation.

## Folder Structure

```
app/
├── core/                    # config, enums, exceptions, shared schemas
├── database/
│   ├── base.py              # Base, mixins
│   ├── session.py           # async engine + FastAPI session DI
│   └── models/              # SQLAlchemy ORM
├── tenants/                 # domain: schemas, repository ABC, service ABC
├── agents/
├── configuration/
├── knowledge/
├── tools/
├── audit/
├── infrastructure/
│   ├── repositories/        # SqlAlchemy*Repository implementations
│   └── services/            # *ServiceImpl (persistence delegation)
├── api/v1/
│   ├── dependencies.py      # FastAPI DI wiring
│   ├── enterprise_router.py # REST route aggregation
│   └── endpoints/           # thin handlers
├── services/                # EXISTING streaming pipeline (unchanged)
├── telephony/               # EXISTING Twilio handler (unchanged)
└── main.py                  # lifespan: init/close database
```

## REST API Surface

All routes are under `/api/v1` (see OpenAPI at `/docs` when `DEBUG=true`).

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/tenants` | Create tenant |
| `GET` | `/tenants` | List tenants |
| `GET` | `/tenants/{tenant_id}` | Get tenant |
| `PATCH` | `/tenants/{tenant_id}` | Update tenant |
| `DELETE` | `/tenants/{tenant_id}` | Delete tenant |
| `POST` | `/tenants/{tenant_id}/agents` | Create agent |
| `GET` | `/tenants/{tenant_id}/agents` | List agents |
| … | `/tenants/{tenant_id}/agents/{agent_id}/configuration` | Agent config CRUD |
| … | `/tenants/{tenant_id}/knowledge-bases` | Knowledge base CRUD |
| … | `/tenants/{tenant_id}/tools` | Tool registry CRUD |
| … | `/tenants/{tenant_id}/audit-logs` | Audit log append + query |

**Voice WebSocket** remains at `WS /api/v1/` — mounted without prefix, unchanged.

## Dependency Injection

FastAPI dependencies in `app/api/v1/dependencies.py`:

1. `_require_database()` — returns 503 if `DATABASE_URL` is unset
2. `get_session()` — async SQLAlchemy session (commit on success)
3. `get_*_service()` — constructs `*ServiceImpl` with `SqlAlchemy*Repository(session)`

Services depend on repository **interfaces**, not SQLAlchemy directly — enabling in-memory or alternate stores in tests.

## Database Setup

1. Start PostgreSQL (example with Docker):

```bash
docker run -d --name voxera-pg \
  -e POSTGRES_USER=voxera \
  -e POSTGRES_PASSWORD=voxera \
  -e POSTGRES_DB=voxera \
  -p 5432:5432 \
  postgres:16
```

2. Configure `.env`:

```env
DATABASE_URL=postgresql+asyncpg://voxera:voxera@localhost:5432/voxera
```

3. Run migrations:

```bash
alembic upgrade head
```

4. Start the backend — enterprise APIs activate automatically when `DATABASE_URL` is set.

Without `DATABASE_URL`, the voice pipeline runs normally; enterprise REST endpoints return **503 Service Unavailable**.

## Migrations

Alembic is configured in `alembic.ini` with async support via `alembic/env.py`. Initial migration: `001_initial_enterprise_schema`.

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "describe change"

# Apply
alembic upgrade head
```

## Sprint 2 Roadmap (not in scope)

- Authentication / API keys / tenant context middleware
- Business rules (slug uniqueness, plan limits, soft-delete)
- Audit auto-recording on mutations
- Wire agent config into streaming voice runtime
- Dashboard → REST integration

## What Was Not Modified

- `app/api/v1/endpoints/websocket.py`
- `app/services/streaming_*`, pipeline managers, turn manager
- `app/telephony/twilio_handler.py`
- WebSocket receive loop, 20ms dispatcher, STT/LLM/TTS consumers
