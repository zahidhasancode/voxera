"""CallSession abstraction for tracking call lifecycle and timestamps."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CallState(str, Enum):
    """Call session lifecycle states."""

    CONNECTED = "connected"
    LISTENING = "listening"
    RESPONDING = "responding"
    ESCALATED = "escalated"
    ENDED = "ended"


class CallSession(BaseModel):
    """Call session abstraction with lifecycle tracking and latency measurement."""

    call_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique call session identifier",
    )
    state: CallState = Field(
        default=CallState.CONNECTED,
        description="Current call session state",
    )
    timestamps: Dict[str, datetime] = Field(
        default_factory=dict,
        description="Timestamps for each state transition",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional session metadata",
    )
    asr_latencies: List[float] = Field(
        default_factory=list,
        description="ASR latency measurements in milliseconds (audio_in → partial_transcript)",
    )

    model_config = {"frozen": False}  # Allow state mutations

    def __init__(self, **kwargs):
        """Initialize call session with creation timestamp."""
        if "call_id" not in kwargs:
            kwargs["call_id"] = str(uuid.uuid4())

        super().__init__(**kwargs)

        # Set initial connected timestamp if not provided
        if CallState.CONNECTED.value not in self.timestamps:
            self.timestamps[CallState.CONNECTED.value] = datetime.now(timezone.utc)

    def transition_to(self, new_state: CallState) -> None:
        """Transition to a new state and record timestamp.

        Args:
            new_state: The new state to transition to

        Raises:
            ValueError: If transition is invalid
        """
        if new_state == self.state:
            return  # Already in this state

        # Validate state transitions
        valid_transitions = {
            CallState.CONNECTED: [
                CallState.LISTENING,
                CallState.ENDED,
            ],
            CallState.LISTENING: [
                CallState.RESPONDING,
                CallState.ESCALATED,
                CallState.ENDED,
            ],
            CallState.RESPONDING: [
                CallState.LISTENING,
                CallState.ESCALATED,
                CallState.ENDED,
            ],
            CallState.ESCALATED: [
                CallState.ENDED,
            ],
            CallState.ENDED: [],  # Terminal state
        }

        allowed = valid_transitions.get(self.state, [])
        if new_state not in allowed and new_state != CallState.ENDED:
            raise ValueError(
                f"Invalid state transition from {self.state.value} to {new_state.value}"
            )

        # Record timestamp for the new state
        self.timestamps[new_state.value] = datetime.now(timezone.utc)
        self.state = new_state

    def get_timestamp(self, state: CallState) -> Optional[datetime]:
        """Get timestamp for a specific state.

        Args:
            state: The state to get timestamp for

        Returns:
            Timestamp if state was reached, None otherwise
        """
        return self.timestamps.get(state.value)

    def get_latency(self, from_state: CallState, to_state: CallState) -> Optional[float]:
        """Calculate latency between two states in seconds.

        Args:
            from_state: Starting state
            to_state: Ending state

        Returns:
            Latency in seconds if both states have timestamps, None otherwise
        """
        from_ts = self.get_timestamp(from_state)
        to_ts = self.get_timestamp(to_state)

        if from_ts and to_ts:
            return (to_ts - from_ts).total_seconds()
        return None

    def get_total_duration(self) -> Optional[float]:
        """Get total session duration in seconds.

        Returns:
            Duration in seconds if session has started and ended, None otherwise
        """
        started = self.get_timestamp(CallState.CONNECTED)
        ended = self.get_timestamp(CallState.ENDED)

        if started and ended:
            return (ended - started).total_seconds()
        return None

    def is_ended(self) -> bool:
        """Check if session has ended."""
        return self.state == CallState.ENDED

    def is_active(self) -> bool:
        """Check if session is currently active (not ended)."""
        return self.state != CallState.ENDED

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def record_asr_latency(self, latency_ms: float) -> None:
        """Record an ASR latency measurement.

        Args:
            latency_ms: Latency in milliseconds (audio_in → partial_transcript)
        """
        self.asr_latencies.append(latency_ms)

    def get_asr_latency_percentiles(self) -> Dict[str, float]:
        """Calculate p50 and p95 ASR latency percentiles.

        Returns:
            Dictionary with 'p50' and 'p95' latency values in milliseconds,
            or empty dict if no latencies recorded
        """
        if not self.asr_latencies:
            return {}

        sorted_latencies = sorted(self.asr_latencies)
        count = len(sorted_latencies)

        def percentile(p: float) -> float:
            """Calculate percentile value."""
            index = (p / 100.0) * (count - 1)
            lower = int(index)
            upper = min(lower + 1, count - 1)
            weight = index - lower
            return sorted_latencies[lower] * (1 - weight) + sorted_latencies[upper] * weight

        return {
            "p50": percentile(50.0),
            "p95": percentile(95.0),
        }

    def get_asr_latency_stats(self) -> Dict[str, Any]:
        """Get ASR latency statistics.

        Returns:
            Dictionary with latency statistics (count, min, max, avg, p50, p95)
        """
        if not self.asr_latencies:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "avg": None,
                "p50": None,
                "p95": None,
            }

        sorted_latencies = sorted(self.asr_latencies)
        count = len(sorted_latencies)

        def percentile(p: float) -> float:
            """Calculate percentile value."""
            index = (p / 100.0) * (count - 1)
            lower = int(index)
            upper = min(lower + 1, count - 1)
            weight = index - lower
            return sorted_latencies[lower] * (1 - weight) + sorted_latencies[upper] * weight

        return {
            "count": count,
            "min": min(sorted_latencies),
            "max": max(sorted_latencies),
            "avg": sum(sorted_latencies) / count,
            "p50": percentile(50.0),
            "p95": percentile(95.0),
        }

    def to_dict(self) -> dict:
        """Convert session to dictionary representation."""
        return {
            "call_id": self.call_id,
            "state": self.state.value,
            "timestamps": {
                k: v.isoformat() if isinstance(v, datetime) else v
                for k, v in self.timestamps.items()
            },
            "metadata": self.metadata,
            "asr_latencies": self.asr_latencies,
            "asr_latency_stats": self.get_asr_latency_stats(),
        }

    def __repr__(self) -> str:
        """String representation of call session."""
        return (
            f"CallSession(call_id={self.call_id}, "
            f"state={self.state.value}, "
            f"timestamps={len(self.timestamps)})"
        )
