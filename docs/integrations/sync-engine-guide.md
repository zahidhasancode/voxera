# Sync Engine Guide

## Trigger sync

```bash
POST /api/v1/tenants/{tenant_id}/integrations/sync
{
  "connection_id": "...",
  "sync_mode": "incremental",
  "entity_types": ["customer", "order"]
}
```

Returns `202 Accepted` with sync job ID.

## Background worker

`IntegrationSyncWorker` processes jobs asynchronously:

1. Load connection + decrypted credentials
2. Load field mappings and cursors
3. Call `SyncEngine.run_sync()`
4. Update cursors and connection `last_sync_at`
5. Retry up to `max_retries`; dead-letter on exhaustion

## Conflict resolution

- **Incremental** — append/upsert records
- **Full** — last-write-wins deduplication by record ID

## Scheduled sync

Configure `sync_schedule_cron` on connection; `IntegrationScheduler.tick()` enqueues due jobs (wire to Celery/APScheduler in production).

## Field mapping

Mappings applied after fetch, before persistence:

```json
{
  "entity_type": "customer",
  "source_field": "properties.email",
  "target_field": "email",
  "transform": {"op": "lowercase"}
}
```
