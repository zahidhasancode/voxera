"""Sync engine — manual, scheduled, webhook, incremental, and full sync."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.enums import IntegrationEntityType, IntegrationSyncMode
from app.integrations.mappings.field_mapper import field_mapper
from app.integrations.monitoring.metrics import integration_metrics
from app.integrations.providers.base import ConnectionContext, SyncFetchResult
from app.integrations.providers.registry import integration_provider_registry


class SyncEngine:
    """Orchestrates entity synchronization with conflict resolution hooks."""

    async def run_sync(
        self,
        *,
        ctx: ConnectionContext,
        entity_types: list[IntegrationEntityType],
        mode: IntegrationSyncMode,
        cursors: dict[str, str | None] | None = None,
    ) -> dict[str, Any]:
        provider = integration_provider_registry.get(ctx.provider_slug)
        started = datetime.now(timezone.utc)

        effective_entities = entity_types or list(
            IntegrationEntityType(e.value) for e in provider.metadata.supported_entities
        )
        cursor_map = cursors or {}

        if mode == IntegrationSyncMode.FULL:
            cursor_map = {e.value: None for e in effective_entities}

        fetch_results: list[SyncFetchResult] = await provider.sync(
            ctx,
            entity_types=effective_entities,
            mode=mode.value,
            cursor=cursor_map,
        )

        normalized: dict[str, list[dict[str, Any]]] = {}
        total_records = 0
        mappings_flat = [
            {"entity_type": et, **m}
            for et, items in ctx.field_mappings.items()
            for m in items
        ]

        for result in fetch_results:
            mapped = field_mapper.apply_mappings(
                result.entity_type.value,
                result.records,
                mappings_flat,
            )
            resolved = self._resolve_conflicts(mapped, mode)
            normalized[result.entity_type.value] = resolved
            total_records += len(resolved)
            if result.next_cursor:
                cursor_map[result.entity_type.value] = result.next_cursor

        elapsed_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000
        integration_metrics.record_sync(ctx.provider_slug, elapsed_ms, success=True)

        return {
            "records_processed": total_records,
            "entities": normalized,
            "cursors": cursor_map,
            "elapsed_ms": round(elapsed_ms, 2),
        }

    def _resolve_conflicts(
        self,
        records: list[dict[str, Any]],
        mode: IntegrationSyncMode,
    ) -> list[dict[str, Any]]:
        """Last-write-wins for incremental; full replace for full sync."""
        if mode != IntegrationSyncMode.FULL:
            return records
        seen: dict[str, dict[str, Any]] = {}
        for record in records:
            key = str(record.get("id") or record.get("_source", {}).get("id") or id(record))
            seen[key] = record
        return list(seen.values())


sync_engine = SyncEngine()
