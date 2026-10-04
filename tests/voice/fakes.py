"""Deterministic fake engines for voice pipeline tests."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Optional, Sequence

from app.llm.streaming_engine import LLMGenerationMetrics, StreamToken, StreamingLLMEngine
from app.tts.streaming_engine import StreamingTTSEngine, TTSAudioMetrics

FRAME = b"\x01\x00" * 320  # 20 ms of PCM16 at 16 kHz


class FakeLLM(StreamingLLMEngine):
    """Yields a fixed answer token by token and records what it was asked."""

    def __init__(self, answer: str = "Sure, I can help. Your order shipped today.", token_delay: float = 0.002) -> None:
        self.answer = answer
        self.token_delay = token_delay
        self.calls: list[dict] = []
        self.fail = False
        self._last_metrics = LLMGenerationMetrics()

    async def stream(
        self,
        prompt: str,
        *,
        utterance_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        history: Optional[Sequence[dict]] = None,
    ) -> AsyncIterator[StreamToken]:
        self.calls.append({"prompt": prompt, "history": list(history or [])})
        if self.fail:
            raise RuntimeError("provider down")
        words = self.answer.split(" ")
        for i, word in enumerate(words):
            await asyncio.sleep(self.token_delay)
            yield StreamToken(token=word + (" " if i < len(words) - 1 else ""), token_index=i)


class FakeTTS(StreamingTTSEngine):
    """Yields `frames_per_segment` frames per text segment and records the segments."""

    def __init__(self, frames_per_segment: int = 5, frame_delay: float = 0.0) -> None:
        self.frames_per_segment = frames_per_segment
        self.frame_delay = frame_delay
        self.segments: list[str] = []
        self._last_metrics = TTSAudioMetrics()

    async def stream(self, text: str, *, utterance_id: str) -> AsyncIterator[bytes]:
        self.segments.append(text)
        for _ in range(self.frames_per_segment):
            await asyncio.sleep(self.frame_delay)
            yield FRAME


class Sink:
    """Collects what a session sends to the client, in order."""

    def __init__(self) -> None:
        self.events: list[object] = []

    async def send_json(self, payload: dict) -> None:
        self.events.append(payload)

    async def send_bytes(self, data: bytes) -> None:
        self.events.append(data)

    def types(self) -> list[str]:
        return [e["type"] if isinstance(e, dict) else "audio" for e in self.events]

    def json(self, kind: str) -> list[dict]:
        return [e for e in self.events if isinstance(e, dict) and e.get("type") == kind]

    def audio_frames(self) -> int:
        return sum(1 for e in self.events if isinstance(e, (bytes, bytearray)))


async def wait_until(predicate, timeout: float = 3.0, interval: float = 0.005) -> None:
    """Poll until predicate() is true; fail the test on timeout."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if predicate():
            return
        await asyncio.sleep(interval)
    raise AssertionError("condition not met within timeout")
