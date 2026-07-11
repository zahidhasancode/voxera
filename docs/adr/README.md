# ADR 0001: Ports and Adapters Architecture

## Status

Accepted

## Context

VOXERA combines a real-time voice stack with an enterprise multi-tenant platform. We need clear boundaries between domain logic, infrastructure, and legacy voice code.

## Decision

Adopt hexagonal architecture:

- **Domain ports** in `app/<module>/services/`, `schemas/`, `api/routes.py`
- **Adapters** in `app/infrastructure/` (repositories, service implementations, factories)
- **Legacy voice** remains in `app/services/`, `app/voice/` during transition

## Consequences

- New enterprise features follow port/adapter pattern
- Factories wire implementations in `dependencies.py`
- Legacy voice stack coexists until unified migration

---

# ADR 0002: In-Process Background Workers

## Status

Accepted (RC1); Redis/Celery deferred to GA

## Context

Knowledge ingestion and integration sync require async job processing.

## Decision

Use asyncio in-process workers with DB-backed job tables (`PersistentIngestionWorker`, `IntegrationSyncWorker`) rather than external queue for RC1.

## Consequences

- Simpler deployment for design partners
- Jobs lost on process crash unless persisted (mitigated by DB job table)
- Horizontal scaling requires job locking (future)

---

# ADR 0003: Tenant-Scoped REST API

## Status

Accepted

## Context

Enterprise customers require strict multi-tenancy.

## Decision

All enterprise resources under `/api/v1/tenants/{tenant_id}/` with middleware tenant access validation and `TenantScopedMixin` on ORM models.

## Consequences

- Cross-tenant access blocked at middleware layer
- Per-route RBAC enforcement planned for GA (see RC1 known issues)

---

# ADR 0004: Structured JSON Logging

## Status

Accepted

## Context

Production operations require searchable, correlatable logs.

## Decision

JSON logs to stdout with `request_id`, `correlation_id`, `tenant_id`, `organization_id`, `user_id`.

## Consequences

- Log aggregation ready
- Trace ID correlation deferred until OpenTelemetry (GA)
