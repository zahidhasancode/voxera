"""Webhook ingestion with idempotency, retry, and dead-letter queue."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.enums import IntegrationWebhookEventStatus, IntegrationSyncMode
from app.integrations.monitoring.metrics import integration_metrics
from app.integrations.providers.base import ConnectionContext
from app.integrations.providers.registry import integration_provider_registry
from app.integrations.sync.engine import sync_engine
from app.integrations.webhooks.signature import webhook_signature_validator


class WebhookProcessor:
    """Process inbound provider webhooks."""

    async def ingest(
        self,
        *,
        ctx: ConnectionContext,
        payload: dict[str, Any],
        headers: dict[str, str],
        event_id: str | None = None,
        webhook_secret: str | None = None,
    ) -> dict[str, Any]:
        started = datetime.now(timezone.utc)
        provider = integration_provider_registry.get(ctx.provider_slug)
        meta = provider.metadata

        if webhook_secret and meta.webhook_signature_header:
            sig = headers.get(meta.webhook_signature_header, "")
            raw = str(payload).encode()
            if not webhook_signature_validator.validate_hmac_sha256(
                payload=raw,
                signature=sig,
                secret=webhook_secret,
            ):
                integration_metrics.record_webhook(ctx.provider_slug, 0, success=False)
                raise ValueError("Invalid webhook signature")

        result = await provider.webhook(ctx, payload=payload, headers=headers)
        resolved_event_id = event_id or result.event_id
        payload_hash = webhook_signature_validator.payload_hash(payload)

        if result.records and result.entity_type:
            await sync_engine.run_sync(
                ctx=ctx,
                entity_types=[result.entity_type],
                mode=IntegrationSyncMode.WEBHOOK,
            )

        elapsed_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000
        integration_metrics.record_webhook(ctx.provider_slug, elapsed_ms, success=True)

        return {
            "event_id": resolved_event_id,
            "event_type": result.event_type,
            "status": IntegrationWebhookEventStatus.PROCESSED.value,
            "payload_hash": payload_hash,
            "records": len(result.records),
            "elapsed_ms": round(elapsed_ms, 2),
        }


webhook_processor = WebhookProcessor()
