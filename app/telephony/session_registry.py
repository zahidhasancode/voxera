"""Active call session registry for concurrency limits and zombie detection."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ActiveCallRecord:
    call_sid: str
    stream_sid: str
    conversation_id: str
    started_at: float = field(default_factory=time.monotonic)
    last_heartbeat: float = field(default_factory=time.monotonic)
    state: str = "connecting"


class CallSessionRegistry:
    """Tracks active telephony sessions and enforces concurrency limits."""

    def __init__(self) -> None:
        self._sessions: dict[str, ActiveCallRecord] = {}
        self._lock = asyncio.Lock()

    async def register(self, *, call_sid: str, stream_sid: str, conversation_id: str) -> None:
        async with self._lock:
            if len(self._sessions) >= settings.VOICE_MAX_CONCURRENT_CALLS:
                raise RuntimeError("Maximum concurrent voice calls reached")
            self._sessions[call_sid] = ActiveCallRecord(
                call_sid=call_sid,
                stream_sid=stream_sid,
                conversation_id=conversation_id,
                state="streaming",
            )
            logger.info(
                "Call session registered",
                extra_fields={
                    "call_sid": call_sid,
                    "active_calls": len(self._sessions),
                    "event": "voice_call_registered",
                },
            )

    async def heartbeat(self, call_sid: str) -> None:
        async with self._lock:
            record = self._sessions.get(call_sid)
            if record:
                record.last_heartbeat = time.monotonic()

    async def update_state(self, call_sid: str, state: str) -> None:
        async with self._lock:
            record = self._sessions.get(call_sid)
            if record:
                record.state = state

    async def unregister(self, call_sid: str) -> None:
        async with self._lock:
            if call_sid in self._sessions:
                del self._sessions[call_sid]
                logger.info(
                    "Call session unregistered",
                    extra_fields={
                        "call_sid": call_sid,
                        "active_calls": len(self._sessions),
                        "event": "voice_call_unregistered",
                    },
                )

    async def snapshot(self) -> list[ActiveCallRecord]:
        async with self._lock:
            return list(self._sessions.values())

    async def cleanup_zombies(self, *, idle_seconds: float | None = None) -> int:
        threshold = idle_seconds or settings.VOICE_IDLE_TIMEOUT_SECONDS
        now = time.monotonic()
        removed = 0
        async with self._lock:
            stale = [
                sid
                for sid, record in self._sessions.items()
                if now - record.last_heartbeat > threshold
            ]
            for sid in stale:
                del self._sessions[sid]
                removed += 1
        if removed:
            logger.warning(
                "Zombie call sessions cleaned",
                extra_fields={"removed": removed, "event": "voice_zombie_cleanup"},
            )
        return removed


call_session_registry = CallSessionRegistry()
