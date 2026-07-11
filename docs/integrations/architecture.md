# Integration Platform Architecture

## Design principles

1. **Plugin architecture** — every provider implements `IntegrationProvider`; no provider-specific logic outside provider modules.
2. **Configurable mappings** — field mappings stored per connection; no hardcoded CRM/helpdesk field maps.
3. **Encrypted credentials** — tokens and API keys encrypted via `SecretProvider`; never returned in API responses.
4. **Tenant isolation** — all connections scoped by `tenant_id` with FK cascade.
5. **Observable** — health, latency, sync failures, webhook status, OAuth refresh metrics.

## Provider contract

```python
class IntegrationProvider(ABC):
    async def connect(ctx, *, redirect_uri) -> ConnectResult
    async def disconnect(ctx) -> None
    async def health(ctx) -> ProviderHealthResult
    async def sync(ctx, *, entity_types, mode, cursor) -> list[SyncFetchResult]
    async def webhook(ctx, *, payload, headers) -> WebhookProcessResult
    async def refresh_token(ctx) -> dict
    async def validate(ctx) -> bool
    async def status(ctx) -> ProviderStatusResult
```

## Sync modes

| Mode | Use case |
|------|----------|
| `manual` | User-triggered from dashboard |
| `scheduled` | Cron via `IntegrationScheduler` |
| `webhook` | Real-time provider events |
| `incremental` | Cursor-based delta sync |
| `full` | Complete re-sync with conflict resolution |

## Data model

- `integration_connections` — tenant connections
- `integration_credentials` — encrypted secrets
- `integration_field_mappings` — per-entity field maps
- `integration_sync_jobs` — background job queue
- `integration_sync_cursors` — incremental sync state
- `integration_webhook_events` — idempotency ledger
- `integration_webhook_dlq` — failed webhook events
- `integration_audit_logs` — audit trail

## Extensibility

Register new providers in `app/integrations/providers/catalog.py` or call `integration_provider_registry.register()` at startup.
