# Webhook Guide

## Inbound URL

```
POST /api/v1/integrations/webhooks/{connection_id}
```

Public (no JWT) — secured by provider signature validation and unguessable connection UUID.

## Features

| Feature | Implementation |
|---------|----------------|
| Signature validation | `WebhookSignatureValidator` HMAC-SHA256 |
| Replay protection | Timestamp header validation (5 min window) |
| Idempotency | Unique `(connection_id, event_id)` in DB |
| Dead letter queue | `integration_webhook_dlq` on processing failure |
| Retry | Re-process from DLQ via admin tooling (future) |

## Provider headers

Each provider declares `webhook_signature_header` in metadata (e.g. `Stripe-Signature`, `X-HubSpot-Signature`).

## Ordering

Events processed in receive order per connection; duplicate `event_id` rejected with `duplicate` status.
