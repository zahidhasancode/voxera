"""STT transcript event models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TranscriptType(str, Enum):
    """Transcript event type."""

    PARTIAL = "partial"
    FINAL = "final"


class TranscriptEvent(BaseModel):
    """STT transcript event."""

    type: TranscriptType = Field(..., description="Transcript type (partial or final)")
    utterance_id: str = Field(..., description="Unique utterance identifier")
    transcript: str = Field(..., description="Transcribed text")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event timestamp",
    )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "utterance_id": self.utterance_id,
            "transcript": self.transcript,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }
