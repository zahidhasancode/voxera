"""Shutdown manager tests."""

import pytest

from app.core.shutdown import ShutdownManager


@pytest.mark.asyncio
async def test_shutdown_tracks_active_requests():
    manager = ShutdownManager()
    await manager.begin_request()
    assert manager.active_requests == 1
    await manager.end_request()
    assert manager.active_requests == 0


@pytest.mark.asyncio
async def test_shutdown_rejects_new_requests_when_draining():
    manager = ShutdownManager()
    manager._shutting_down = True
    with pytest.raises(RuntimeError, match="shutting down"):
        await manager.begin_request()
