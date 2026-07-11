# Enterprise Integration Platform

VOXERA connects to enterprise software automatically — CRM, helpdesk, ecommerce, calendar, email, identity, payments, knowledge, and telephony.

## Architecture

```
app/integrations/
├── api/              # REST + public webhook/OAuth routes
├── providers/        # IntegrationProvider plugin catalog (50+ providers)
├── oauth/            # OAuth2 token lifecycle
├── webhooks/         # Signature validation, idempotency, DLQ
├── sync/             # Manual, scheduled, incremental, full sync
├── scheduler/        # Cron-driven sync submission
├── mappings/         # Configurable field mapping engine
├── credentials/      # Encrypted token/secret storage
├── jobs/             # Background sync worker port
├── monitoring/       # Latency, failures, OAuth refresh metrics
├── repository/       # Persistence port
├── services/         # IntegrationService port
└── schemas/          # API DTOs
```

## API (tenant-scoped)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/tenants/{tenant_id}/integrations` | List connections |
| GET | `/api/v1/tenants/{tenant_id}/integrations/catalog` | Provider catalog |
| POST | `/api/v1/tenants/{tenant_id}/integrations/connect` | Connect provider |
| POST | `/api/v1/tenants/{tenant_id}/integrations/disconnect` | Disconnect |
| GET | `/api/v1/tenants/{tenant_id}/integrations/status/{id}` | Health check |
| GET | `/api/v1/tenants/{tenant_id}/integrations/logs` | Audit logs |
| POST | `/api/v1/tenants/{tenant_id}/integrations/sync` | Trigger sync |
| GET | `/api/v1/tenants/{tenant_id}/integrations/metrics` | Platform metrics |

## Public routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/integrations/oauth/callback` | OAuth callback |
| POST | `/api/v1/integrations/webhooks/{connection_id}` | Inbound webhooks |

## Dashboard

`/app/integrations` — Connected apps, provider catalog, sync, health, logs.

## Documentation

- [Integration Architecture](./architecture.md)
- [Provider Development Guide](./provider-development-guide.md)
- [OAuth Guide](./oauth-guide.md)
- [Webhook Guide](./webhook-guide.md)
- [Sync Engine Guide](./sync-engine-guide.md)

## Migration

```bash
alembic upgrade head  # applies 010_integrations
```
