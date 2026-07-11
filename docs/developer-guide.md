# Developer Guide

## Repository layout

```
app/                    # Backend (FastAPI)
  core/                 # Config, middleware, health, logging
  api/v1/               # HTTP routing and dependencies
  iam/                  # Authentication, RBAC, organizations
  planner/ verifier/ workflow/ tools/ rag/ memory/ knowledge/
  integrations/         # Enterprise integration platform
  voice/ stt/ tts/ llm/ telephony/  # Voice pipeline
  infrastructure/       # Adapters, repos, factories
dashboard/              # Enterprise admin UI
web/                    # Voice demo UI
tests/                  # Python test suites
deploy/                 # Helm, monitoring, env samples
docs/                   # Architecture and operations
```

## Architecture pattern

**Ports and adapters:** Domain logic in `app/<module>/` with ABC service ports; implementations in `app/infrastructure/`.

## Running locally

See [CONTRIBUTING.md](../CONTRIBUTING.md).

## API documentation

- OpenAPI: `http://localhost:8000/docs` (development only)
- Enterprise routes: `/api/v1/tenants/{tenant_id}/...`
- IAM routes: `/api/v1/iam/...`

## Testing

See [docs/testing/qa-guide.md](testing/qa-guide.md).

## Environment variables

See [docs/operations/environment-variables.md](operations/environment-variables.md).

## Adding a domain module

1. Create `app/mymodule/` with schemas, service ABC, `api/routes.py`
2. Add ORM models + Alembic migration
3. Implement in `app/infrastructure/`
4. Register in `enterprise_router.py` and `dependencies.py`

## Release process

See [docs/release/release-checklist.md](release/release-checklist.md).
