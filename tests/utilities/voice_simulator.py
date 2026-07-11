"""Voice conversation simulation for enterprise QA."""

from __future__ import annotations

import asyncio
import random
import struct
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Callable, Awaitable


class SpeechRate(str, Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


class AccentProfile(str, Enum):
    NEUTRAL = "neutral"
    BRITISH = "british"
    SOUTHERN_US = "southern_us"
    NON_NATIVE = "non_native"


@dataclass
class VoiceScenario:
    """Configurable voice call simulation parameters."""

    name: str
    speech_rate: SpeechRate = SpeechRate.NORMAL
    accent: AccentProfile = AccentProfile.NEUTRAL
    language: str = "en-US"
    secondary_language: str | None = None
    noise_level: float = 0.0  # 0.0 - 1.0 amplitude mix
    silence_gaps_ms: list[int] = field(default_factory=list)
    interruption_at_ms: list[int] = field(default_factory=list)
    packet_loss_rate: float = 0.0  # 0.0 - 1.0
    network_delay_ms: int = 0
    frame_duration_ms: int = 20
    sample_rate_hz: int = 8000
    duration_ms: int = 3000
    multi_speaker_turns: int = 1
    barge_in_enabled: bool = False

    @property
    def frame_size_bytes(self) -> int:
        samples = int(self.sample_rate_hz * self.frame_duration_ms / 1000)
        return samples * 2  # 16-bit PCM


@dataclass
class SimulationMetrics:
    frames_sent: int = 0
    frames_dropped: int = 0
    interruptions_triggered: int = 0
    total_latency_ms: float = 0.0
    elapsed_ms: float = 0.0


class VoiceSimulator:
    """Generates PCM audio frames and simulates network/voice conditions."""

    def __init__(self, scenario: VoiceScenario):
        self.scenario = scenario
        self.metrics = SimulationMetrics()

    def _silence_frame(self) -> bytes:
        return b"\x00" * self.scenario.frame_size_bytes

    def _tone_frame(self, amplitude: int = 8000) -> bytes:
        samples = self.scenario.frame_size_bytes // 2
        return struct.pack(f"<{samples}h", *([amplitude] * samples))

    def _apply_noise(self, frame: bytes) -> bytes:
        if self.scenario.noise_level <= 0:
            return frame
        samples = len(frame) // 2
        values = struct.unpack(f"<{samples}h", frame)
        noisy = []
        for v in values:
            noise = int(random.uniform(-32767, 32767) * self.scenario.noise_level * 0.1)
            noisy.append(max(-32768, min(32767, v + noise)))
        return struct.pack(f"<{samples}h", *noisy)

    async def stream_frames(self) -> AsyncIterator[bytes]:
        """Yield PCM frames with simulated conditions."""
        total_frames = max(1, self.scenario.duration_ms // self.scenario.frame_duration_ms)
        start = time.perf_counter()
        silence_set = set(self.scenario.silence_gaps_ms)
        interrupt_set = set(self.scenario.interruption_at_ms)

        for index in range(total_frames):
            elapsed_ms = index * self.scenario.frame_duration_ms

            if random.random() < self.scenario.packet_loss_rate:
                self.metrics.frames_dropped += 1
                continue

            if elapsed_ms in silence_set:
                frame = self._silence_frame()
            else:
                rate_factor = {
                    SpeechRate.SLOW: 0.5,
                    SpeechRate.NORMAL: 1.0,
                    SpeechRate.FAST: 2.0,
                }[self.scenario.speech_rate]
                if int(index * rate_factor) % 3 == 0:
                    frame = self._tone_frame()
                else:
                    frame = self._silence_frame()

            frame = self._apply_noise(frame)
            self.metrics.frames_sent += 1

            if elapsed_ms in interrupt_set and self.scenario.barge_in_enabled:
                self.metrics.interruptions_triggered += 1

            if self.scenario.network_delay_ms:
                await asyncio.sleep(self.scenario.network_delay_ms / 1000.0)

            yield frame
            await asyncio.sleep(self.scenario.frame_duration_ms / 1000.0)

        self.metrics.elapsed_ms = (time.perf_counter() - start) * 1000.0

    async def run_with_handler(
        self,
        frame_handler: Callable[[bytes, int], Awaitable[None]],
    ) -> SimulationMetrics:
        """Stream frames to an async handler (frame, index)."""
        index = 0
        async for frame in self.stream_frames():
            await frame_handler(frame, index)
            index += 1
        return self.metrics


def standard_scenarios() -> dict[str, VoiceScenario]:
    """Built-in scenarios for regression suites."""
    return {
        "normal_conversation": VoiceScenario(name="normal_conversation", duration_ms=5000),
        "fast_speech": VoiceScenario(
            name="fast_speech",
            speech_rate=SpeechRate.FAST,
            duration_ms=4000,
        ),
        "slow_speech": VoiceScenario(
            name="slow_speech",
            speech_rate=SpeechRate.SLOW,
            duration_ms=6000,
        ),
        "noisy_line": VoiceScenario(
            name="noisy_line",
            noise_level=0.35,
            duration_ms=4000,
        ),
        "packet_loss": VoiceScenario(
            name="packet_loss",
            packet_loss_rate=0.08,
            network_delay_ms=40,
            duration_ms=4000,
        ),
        "barge_in": VoiceScenario(
            name="barge_in",
            barge_in_enabled=True,
            interruption_at_ms=[1000, 2000],
            duration_ms=5000,
        ),
        "long_conversation": VoiceScenario(
            name="long_conversation",
            duration_ms=60_000,
            multi_speaker_turns=4,
        ),
        "language_switch": VoiceScenario(
            name="language_switch",
            language="en-US",
            secondary_language="es-ES",
            duration_ms=5000,
        ),
    }
