# Platform Reliability Architecture

VOXERA's reliability layer hardens the HTTP boundary without changing domain business logic (planner, verifier, workflow, memory, tools, voice pipeline).

## Middleware Flow (inbound request order)

```
Client
  → CORSMiddleware
  → RateLimitMiddleware
  → RequestTimeoutMiddleware
  → RequestContextMiddleware   (request_id, correlation_id, timing, metrics)
  → AuthenticationMiddleware   (JWT / API key, tenant/org authorization)
  → FastAPI route handler
  → Global exception handlers
```

### Headers

| Header | Purpose |
|--------|---------|
| `X-Request-ID` | Unique per-request identifier (generated if absent) |
| `X-Correlation-ID` | Cross-service trace correlation (defaults to request ID) |
| `X-Call-ID` | Voice call correlation |
| `X-Process-Time-Ms` | Server-side latency |

## Standard Error Envelope

All errors return:

```json
{
  "success": false,
  "error": {
    "code": "authentication_error",
    "message": "Human-readable message",
    "details": {},
    "request_id": "uuid",
    "timestamp": "2026-07-11T00:00:00+00:00",
    "documentation_url": "https://docs.voxera.ai/errors/authentication_error"
  }
}
```

Stack traces are never exposed to clients. Unknown exceptions map to `internal_error` (HTTP 500).

## Health Endpoints

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `GET /api/v1/health/live` | Process liveness | Public |
| `GET /api/v1/health/ready` | Dependency readiness | Public |
| `GET /api/v1/health/deep` | Extended diagnostics + platform metrics | Public |
| `GET /api/v1/health` | Legacy readiness + streaming metrics | Public |

### Readiness checks

- Database connectivity + Alembic migration version
- Knowledge storage path writable
- Embedding / vector provider configuration status
- Domain module loadability (planner, verifier, workflow, tools, memory, rag)
- Redis / queue (skipped — future)

Status values: `healthy`, `degraded`, `unhealthy`, `skipped`.

## Rate Limiting

In-process sliding window (per worker). Configurable via environment:

- Per IP
- Per endpoint (`METHOD:path`)
- Per API key prefix
- Per organization / tenant (when authenticated)

Returns HTTP 429 with `Retry-After` header and `rate_limit_exceeded` error code.

## Request Timeouts

Configurable per route class:

| Path pattern | Default timeout |
|--------------|-----------------|
| `/knowledge`, `/rag` | 45s |
| `/planner` | 60s |
| `/verifier` | 60s |
| `/tools` | 45s |
| `/workflow` | 90s |
| Default | 30s |

Returns HTTP 504 with `request_timeout` error code.

## Graceful Shutdown

On application shutdown (SIGTERM via uvicorn):

1. Mark server as draining — reject new API requests with 503
2. Wait for in-flight HTTP requests (configurable drain timeout)
3. Close all WebSocket connections
4. Dispose database engine
5. Flush logs

## Observability

In-process `platform_metrics` tracks:

- Request count, error count
- Latency avg / P95 / P99
- Timeout and rate-limit counts
- Exception type counts
- Dependency failure counts

Exposed via `GET /api/v1/health/deep`.

Structured logs include: `request_id`, `correlation_id`, `tenant_id`, `organization_id`, `user_id`, `method`, `endpoint`, `status_code`, `latency_ms`.

## API Versioning

All enterprise routes remain under `/api/v1/`. Reliability changes are backward compatible — legacy `GET /api/v1/health` preserved with enhanced semantics.
