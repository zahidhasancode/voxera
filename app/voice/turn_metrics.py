"""Per-turn voice latency: what a caller actually waits for.

The clock starts when the final transcript of the user's turn arrives (the
moment the pipeline knows the user has finished) and stops at the first LLM
token and at the first audio frame sent back. End-of-speech detection time in
the STT provider is not included here, because the server cannot see when the
user really stopped talking; the benchmark client measures that from outside
(see scripts/bench_voice_latency.py).
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional


@dataclass
class TurnTiming:
    """Timestamps (time.monotonic) for one user turn and the reply to it."""

    utterance_id: str
    transcript_final_at: float = field(default_factory=time.monotonic)
    llm_first_token_at: Optional[float] = None
    first_segment_at: Optional[float] = None
    first_audio_at: Optional[float] = None
    interrupted: bool = False

    def mark_llm_first_token(self) -> None:
        if self.llm_first_token_at is None:
            self.llm_first_token_at = time.monotonic()

    def mark_first_segment(self) -> None:
        if self.first_segment_at is None:
            self.first_segment_at = time.monotonic()

    def mark_first_audio(self) -> None:
        if self.first_audio_at is None:
            self.first_audio_at = time.monotonic()

    @staticmethod
    def _ms(start: Optional[float], end: Optional[float]) -> Optional[float]:
        if start is None or end is None:
            return None
        return round((end - start) * 1000.0, 1)

    def to_payload(self) -> dict:
        return {
            "type": "turn_metrics",
            "utterance_id": self.utterance_id,
            "transcript_final_to_llm_first_token_ms": self._ms(self.transcript_final_at, self.llm_first_token_at),
            "transcript_final_to_first_segment_ms": self._ms(self.transcript_final_at, self.first_segment_at),
            "transcript_final_to_first_audio_ms": self._ms(self.transcript_final_at, self.first_audio_at),
            "llm_first_token_to_first_audio_ms": self._ms(self.llm_first_token_at, self.first_audio_at),
            "interrupted": self.interrupted,
        }


def _percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    idx = min(len(sorted_values) - 1, max(0, round(q * (len(sorted_values) - 1))))
    return sorted_values[idx]


class VoiceLatencyStats:
    """Rolling window of per-turn latencies for the metrics endpoint."""

    def __init__(self, max_samples: int = 500) -> None:
        self._first_audio: deque[float] = deque(maxlen=max_samples)
        self._first_token: deque[float] = deque(maxlen=max_samples)
        self._barge_in_stop: deque[float] = deque(maxlen=max_samples)
        self._turns = 0
        self._interruptions = 0
        self._lock = Lock()

    def record_turn(self, timing: TurnTiming) -> None:
        payload = timing.to_payload()
        with self._lock:
            self._turns += 1
            if payload["transcript_final_to_first_audio_ms"] is not None:
                self._first_audio.append(payload["transcript_final_to_first_audio_ms"])
            if payload["transcript_final_to_llm_first_token_ms"] is not None:
                self._first_token.append(payload["transcript_final_to_llm_first_token_ms"])

    def record_barge_in(self, stop_ms: float) -> None:
        with self._lock:
            self._interruptions += 1
            self._barge_in_stop.append(round(stop_ms, 2))

    def snapshot(self) -> dict:
        with self._lock:
            audio = sorted(self._first_audio)
            token = sorted(self._first_token)
            stop = sorted(self._barge_in_stop)
            return {
                "turns": self._turns,
                "interruptions": self._interruptions,
                "first_audio_p50_ms": _percentile(audio, 0.50),
                "first_audio_p95_ms": _percentile(audio, 0.95),
                "llm_first_token_p50_ms": _percentile(token, 0.50),
                "llm_first_token_p95_ms": _percentile(token, 0.95),
                "barge_in_stop_p50_ms": _percentile(stop, 0.50),
                "barge_in_stop_p95_ms": _percentile(stop, 0.95),
                "samples": len(audio),
            }

    def reset(self) -> None:
        with self._lock:
            self._first_audio.clear()
            self._first_token.clear()
            self._barge_in_stop.clear()
            self._turns = 0
            self._interruptions = 0


voice_latency_stats = VoiceLatencyStats()
