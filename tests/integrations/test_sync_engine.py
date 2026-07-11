"""Sync engine tests."""

from uuid import uuid4

import pytest

from app.core.enums import IntegrationEntityType, IntegrationSyncMode
from app.integrations.providers.base import ConnectionContext
from app.integrations.sync.engine import sync_engine


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_engine_runs_without_records():
    ctx = ConnectionContext(
        tenant_id=uuid4(),
        connection_id=uuid4(),
        provider_slug="stripe",
        config={},
        credentials={"api_key": "sk_test_123"},
    )
    result = await sync_engine.run_sync(
        ctx=ctx,
        entity_types=[IntegrationEntityType.ORDER],
        mode=IntegrationSyncMode.INCREMENTAL,
    )
    assert "records_processed" in result
    assert result["records_processed"] >= 0
