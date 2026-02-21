"""Call performance metrics for Twilio call sessions.

Dataclass and computed properties for latency and duration.
Measurement only; no business logic.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CallPerformanceMetrics:
    """Per-call performance timestamps (monotonic seconds).

    Set by measurement hooks; computed properties derive latencies in ms.
    """

    call_sid: str
    call_start_time: float
    first_user_audio_time: Optional[float] = None
    first_transcript_time: Optional[float] = None
    first_token_time: Optional[float] = None
    first_audio_response_time: Optional[float] = None
    call_end_time: Optional[float] = None

    @property
    def call_duration_ms(self) -> Optional[float]:
        """Total call duration in milliseconds. None if call not ended."""
        if self.call_end_time is None:
            return None
        return (self.call_end_time - self.call_start_time) * 1000.0

    @property
    def first_transcript_latency_ms(self) -> Optional[float]:
        """Time from first user audio to first STT transcript (ms)."""
        if self.first_user_audio_time is None or self.first_transcript_time is None:
            return None
        return (self.first_transcript_time - self.first_user_audio_time) * 1000.0

    @property
    def first_token_latency_ms(self) -> Optional[float]:
        """Time from first transcript to first LLM token (ms)."""
        if self.first_transcript_time is None or self.first_token_time is None:
            return None
        return (self.first_token_time - self.first_transcript_time) * 1000.0

    @property
    def first_audio_latency_ms(self) -> Optional[float]:
        """Time from first user audio to first TTS frame sent (ms)."""
        if self.first_user_audio_time is None or self.first_audio_response_time is None:
            return None
        return (self.first_audio_response_time - self.first_user_audio_time) * 1000.0

    @property
    def total_turn_latency_ms(self) -> Optional[float]:
        """Time from first transcript to first TTS frame sent (ms)."""
        if self.first_transcript_time is None or self.first_audio_response_time is None:
            return None
        return (self.first_audio_response_time - self.first_transcript_time) * 1000.0

    def to_log_dict(self) -> dict[str, Any]:
        """Structured dict for JSON logging (raw times + computed ms)."""
        return {
            "call_sid": self.call_sid,
            "call_start_time": self.call_start_time,
            "first_user_audio_time": self.first_user_audio_time,
            "first_transcript_time": self.first_transcript_time,
            "first_token_time": self.first_token_time,
            "first_audio_response_time": self.first_audio_response_time,
            "call_end_time": self.call_end_time,
            "call_duration_ms": self.call_duration_ms,
            "first_transcript_latency_ms": self.first_transcript_latency_ms,
            "first_token_latency_ms": self.first_token_latency_ms,
            "first_audio_latency_ms": self.first_audio_latency_ms,
            "total_turn_latency_ms": self.total_turn_latency_ms,
        }
