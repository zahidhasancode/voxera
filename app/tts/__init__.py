"""TTS streaming engine and consumer for VOXERA.

Supports pluggable backends (mock, cloud TTS, local synthesis).
"""

from app.tts.streaming_engine import (
    MockStreamingTTSEngine,
    StreamingTTSEngine,
    TTSAudioMetrics,
)
from app.tts.tts_consumer import TTSConsumer

__all__ = [
    "MockStreamingTTSEngine",
    "StreamingTTSEngine",
    "TTSAudioMetrics",
    "TTSConsumer",
]
