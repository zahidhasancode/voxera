"""Streaming TTS engine with async generator, cancellation, and audio metrics.

Designed to mirror StreamingLLMEngine: pluggable backends, async iterators,
cancellation via asyncio, and last_metrics() for instrumentation.
"""

import asyncio
import math
import random
import struct
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TTSAudioMetrics:
    """Latency and throughput metrics for one TTS stream."""

    time_to_first_audio_ms: float = 0.0
    total_audio_ms: float = 0.0
    frame_count: int = 0
    frames_per_second: float = 0.0

    def to_dict(self) -> dict:
        """Serialize for WebSocket/JSON."""
        return {
            "time_to_first_audio_ms": round(self.time_to_first_audio_ms, 2),
            "total_audio_ms": round(self.total_audio_ms, 2),
            "frame_count": self.frame_count,
            "frames_per_second": round(self.frames_per_second, 2),
        }


class StreamingTTSEngine(ABC):
    """Abstract streaming TTS engine.

    Implementations: MockStreamingTTSEngine, cloud TTS, local synthesis.
    """

    @abstractmethod
    async def stream(self, text: str, *, utterance_id: str) -> AsyncIterator[bytes]:
        """Stream raw PCM16 mono audio chunks (20ms frames) for the given text.

        Yields bytes. Cancellation (e.g. barge-in) is delivered by the
        event loop when the consuming task is cancelled; implementations
        should use await asyncio.sleep(...) or similar to allow delivery.

        After the generator exits (normally or cancelled), metrics are
        available via last_metrics().

        Args:
            text: Text to synthesize.
            utterance_id: Utterance ID for tracing.

        Yields:
            Raw PCM16 mono audio chunks (20ms frames).
        """
        ...

    def last_metrics(self) -> TTSAudioMetrics:
        """Return metrics from the most recent stream() run.

        Valid after the async iterator is exhausted or cancelled.
        """
        return getattr(self, "_last_metrics", None) or TTSAudioMetrics()


class MockStreamingTTSEngine(StreamingTTSEngine):
    """Mock streaming TTS for development and testing.

    - Emits PCM16 mono 20ms frames with silence or a low-amplitude tone.
    - Per-word frame generation with 15–30 ms delay between frames.
    - Supports interruption via asyncio cancellation.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 20,
        min_frame_delay_ms: float = 15.0,
        max_frame_delay_ms: float = 30.0,
    ):
        """Initialize mock engine.

        Args:
            sample_rate: Sample rate in Hz (default 16000).
            frame_duration_ms: Duration of each frame in ms (default 20).
            min_frame_delay_ms: Minimum delay between frames in ms (default 15).
            max_frame_delay_ms: Maximum delay between frames in ms (default 30).
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.min_frame_delay_ms = min_frame_delay_ms
        self.max_frame_delay_ms = max_frame_delay_ms
        # PCM16: 2 bytes per sample. Frames: sample_rate * (frame_duration_ms/1000) samples
        samples_per_frame = int(sample_rate * (frame_duration_ms / 1000.0))
        self._frame_size = samples_per_frame * 2
        self._last_metrics: TTSAudioMetrics = TTSAudioMetrics()

    def _make_frame(self, use_tone: bool = False) -> bytes:
        """Generate one PCM16 mono frame: silence (zeros) or a low-amplitude tone."""
        n = self._frame_size // 2  # number of 16-bit samples
        if use_tone:
            # 200 Hz tone at low amplitude to simulate voice
            amp = 1000
            freq = 200.0
            return struct.pack(
                f"<{n}h",
                *(
                    int(amp * math.sin(2 * math.pi * freq * i / self.sample_rate))
                    for i in range(n)
                ),
            )
        return bytes(self._frame_size)

    async def stream(self, text: str, *, utterance_id: str) -> AsyncIterator[bytes]:
        """Stream mock PCM16 frames: for each word, N frames with random delay."""
        words = text.split() or ["(silence)"]
        start = time.monotonic()
        first_audio_time: float | None = None
        frame_count = 0

        try:
            for wi, word in enumerate(words):
                # Frames per word: 2 + length-based, at least 1
                n_frames = max(1, 2 + len(word) // 2)
                for fi in range(n_frames):
                    delay_ms = random.uniform(
                        self.min_frame_delay_ms,
                        self.max_frame_delay_ms,
                    )
                    await asyncio.sleep(delay_ms / 1000.0)

                    if first_audio_time is None:
                        first_audio_time = time.monotonic()

                    frame_count += 1
                    # Alternate silence/tone for variety
                    yield self._make_frame(use_tone=(fi % 2 == 1))

        except asyncio.CancelledError:
            logger.info(
                "Mock TTS stream cancelled (barge-in)",
                extra_fields={
                    "utterance_id": utterance_id,
                    "frames_emitted": frame_count,
                },
            )
            raise
        finally:
            end = time.monotonic()
            ttfa_ms = (first_audio_time - start) * 1000.0 if first_audio_time else 0.0
            total_ms = (end - start) * 1000.0
            fps = (frame_count / (total_ms / 1000.0)) if total_ms > 0 else 0.0
            self._last_metrics = TTSAudioMetrics(
                time_to_first_audio_ms=ttfa_ms,
                total_audio_ms=total_ms,
                frame_count=frame_count,
                frames_per_second=fps,
            )

    def last_metrics(self) -> TTSAudioMetrics:
        return self._last_metrics
