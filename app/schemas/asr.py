"""ASR (Automatic Speech Recognition) schemas."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TranscriptType(str, Enum):
    """Transcript type enumeration."""

    PARTIAL = "partial"  # Interim/partial transcript
    FINAL = "final"  # Final confirmed transcript


class TranscriptResult(BaseModel):
    """ASR transcript result."""

    transcript: str = Field(..., description="Transcribed text")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)",
    )
    type: TranscriptType = Field(..., description="Transcript type (partial or final)")
    call_id: str = Field(..., description="Call session ID")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    is_final: bool = Field(..., description="Whether this is a final transcript")


@dataclass
class PartialTranscript:
    """Partial transcript data structure."""

    text: str
    confidence: float
    call_id: str
    timestamp: datetime
