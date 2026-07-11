# Environment Variables Guide

## Environments

| Environment | File | Validation |
|-------------|------|------------|
| Development | `.env` | Relaxed; `SECRET_KEY` fallback allowed |
| Testing | CI env vars | Test secrets injected in GitHub Actions |
| Staging | `.env.staging` / K8s secrets | Full secret validation |
| Production | `.env.production` / K8s secrets | Fail fast on missing secrets |

Templates:
- `.env.example` — full reference (repo root)
- `deploy/env/.env.production.example` — production subset

## Required in Production (when DATABASE_URL set)

| Variable | Min length | Purpose |
|----------|------------|---------|
| `JWT_SECRET_KEY` | 32 | JWT signing |
| `API_KEY_SECRET` | 32 | API key HMAC |
| `ENCRYPTION_SECRET_KEY` | 32 | Field encryption |
| `DATABASE_URL` | — | PostgreSQL connection |

## Startup Validation

Container entrypoint runs `scripts/validate-env.py` when `VALIDATE_CONFIG=true`.

Application lifespan calls `settings.validate_security_settings()`.

## Secrets Management

| Provider | Config | Status |
|----------|--------|--------|
| Local env / K8s Secret | `IAM_SECRET_PROVIDER=local` | **Active** |
| AWS Secrets Manager | `IAM_SECRET_PROVIDER=aws` | Planned |
| Azure Key Vault | `IAM_SECRET_PROVIDER=azure` | Planned |
| GCP Secret Manager | `IAM_SECRET_PROVIDER=gcp` | Planned |
| HashiCorp Vault | `IAM_SECRET_PROVIDER=vault` | Planned |

Never commit secrets. Use:

```bash
openssl rand -base64 32
```

## Container-Specific

| Variable | Default | Purpose |
|----------|---------|---------|
| `RUN_MIGRATIONS` | `true` | Alembic upgrade on start |
| `VALIDATE_CONFIG` | `true` | Pre-flight env validation |
| `WORKERS` | `4` | Uvicorn worker count |

## Frontend (build-time)

| Variable | App | Purpose |
|----------|-----|---------|
| `VITE_API_URL` | Dashboard | API base path |
| `VITE_WS_URL` | Dashboard, Web | WebSocket URL |

Set as Docker build args in production images.

## Full Reference

See `.env.example` at repository root for all supported variables grouped by subsystem.
