"""Call session registry tests."""

import pytest

from app.telephony.session_registry import CallSessionRegistry


@pytest.mark.asyncio
async def test_register_and_unregister() -> None:
    registry = CallSessionRegistry()
    await registry.register(call_sid="CA1", stream_sid="MS1", conversation_id="conv1")
    snapshot = await registry.snapshot()
    assert len(snapshot) == 1
    await registry.unregister("CA1")
    assert len(await registry.snapshot()) == 0


@pytest.mark.asyncio
async def test_concurrency_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.telephony.session_registry.settings.VOICE_MAX_CONCURRENT_CALLS", 1)
    registry = CallSessionRegistry()
    await registry.register(call_sid="CA1", stream_sid="MS1", conversation_id="conv1")
    with pytest.raises(RuntimeError, match="Maximum concurrent"):
        await registry.register(call_sid="CA2", stream_sid="MS2", conversation_id="conv2")
