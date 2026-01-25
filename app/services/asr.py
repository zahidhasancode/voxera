"""Streaming ASR (Automatic Speech Recognition) interface and implementations."""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Callable, Optional

from app.core.logger import get_logger
from app.models.call_session import CallState
from app.services.audio_output import audio_output_controller
from app.services.audio_pipeline import AudioChunk, AudioConsumer
from app.services.call_session_manager import session_manager

logger = get_logger(__name__)

# ASR latency threshold for fail-fast (milliseconds)
ASR_LATENCY_THRESHOLD_MS = 150.0


class StreamingASR(ABC):
    """Abstract interface for streaming ASR backends."""

    @abstractmethod
    async def process_audio(self, audio_data: bytes) -> Optional[str]:
        """Process audio data and return partial transcript if available.

        Args:
            audio_data: PCM audio bytes

        Returns:
            Partial transcript text if available, None otherwise
        """
        pass

    @abstractmethod
    async def get_confidence(self, transcript: str) -> float:
        """Get confidence score for a transcript.

        Args:
            transcript: Transcribed text

        Returns:
            Confidence score (0.0-1.0)
        """
        pass

    @abstractmethod
    async def reset(self) -> None:
        """Reset ASR state (e.g., on interruption)."""
        pass

    @abstractmethod
    async def finalize(self) -> Optional[str]:
        """Get final transcript.

        Returns:
            Final transcript text or None
        """
        pass


class MockStreamingASR(StreamingASR):
    """Mock ASR implementation for testing and development."""

    def __init__(self, word_probability: float = 0.1):
        """Initialize mock ASR.

        Args:
            word_probability: Probability of generating a word per chunk (0.0-1.0)
        """
        self.word_probability = word_probability
        self.buffer = ""
        self.word_count = 0
        self.mock_words = [
            "hello",
            "yes",
            "no",
            "please",
            "thank",
            "you",
            "help",
            "support",
            "account",
            "balance",
        ]

    async def process_audio(self, audio_data: bytes) -> Optional[str]:
        """Process audio and occasionally return mock transcript.

        Args:
            audio_data: PCM audio bytes

        Returns:
            Mock partial transcript if word generated, None otherwise
        """
        # Randomly generate words based on probability
        if random.random() < self.word_probability:
            word = random.choice(self.mock_words)
            self.buffer += word + " "
            self.word_count += 1

            # Return partial transcript every few words
            if self.word_count % 3 == 0:
                return self.buffer.strip()

        return None

    async def get_confidence(self, transcript: str) -> float:
        """Get mock confidence score.

        Args:
            transcript: Transcribed text

        Returns:
            Random confidence score between 0.7 and 0.99
        """
        # Simulate varying confidence
        return random.uniform(0.7, 0.99)

    async def reset(self) -> None:
        """Reset ASR state."""
        self.buffer = ""
        self.word_count = 0

    async def finalize(self) -> Optional[str]:
        """Get final transcript.

        Returns:
            Final transcript or None if buffer is empty
        """
        result = self.buffer.strip()
        self.buffer = ""
        self.word_count = 0
        return result if result else None


class ASRConsumer(AudioConsumer):
    """ASR consumer that processes audio and emits transcripts."""

    def __init__(
        self,
        asr_backend: StreamingASR,
        name: str = "asr",
        max_queue_size: int = 50,
        emit_interval_ms: int = 75,
        transcript_callback: Optional[Callable[[dict], None]] = None,
        latency_threshold_ms: float = ASR_LATENCY_THRESHOLD_MS,
        stats_log_interval: int = 10,
    ):
        """Initialize ASR consumer.

        Args:
            asr_backend: ASR backend implementation
            name: Consumer name
            max_queue_size: Maximum queue size
            emit_interval_ms: Interval in milliseconds for emitting partial transcripts
            transcript_callback: Optional callback for transcript events
            latency_threshold_ms: Fail-fast threshold for latency in milliseconds
            stats_log_interval: Log latency stats every N transcripts
        """
        super().__init__(name, max_queue_size)
        self.asr_backend = asr_backend
        self.emit_interval_ms = emit_interval_ms
        self.transcript_callback = transcript_callback
        self.latency_threshold_ms = latency_threshold_ms
        self.stats_log_interval = stats_log_interval
        self._chunks_since_emit = 0
        self._last_emit_time: Optional[float] = None
        self._interrupted = False
        self._transcript_count = 0

    async def process_chunk(self, chunk: AudioChunk) -> None:
        """Process audio chunk through ASR.

        Args:
            chunk: Audio chunk to process
        """
        # Track audio_in timestamp for latency measurement
        audio_in_timestamp = chunk.timestamp
        chunk_key = chunk.sequence

        # Check for interruption
        if self._interrupted:
            await self.asr_backend.reset()
            self._interrupted = False

        # Check if output was stopped (barge-in/interruption)
        if audio_output_controller.is_stopped(chunk.call_id):
            self._interrupted = True
            await self.asr_backend.reset()
            return

        # Process audio through ASR backend
        try:
            partial_transcript = await self.asr_backend.process_audio(chunk.data)

            if partial_transcript:
                # Get confidence score
                confidence = await self.asr_backend.get_confidence(partial_transcript)

                # Emit partial transcript based on interval
                should_emit = self._should_emit_partial()

                if should_emit:
                    # Measure and record latency
                    await self._emit_partial_transcript(
                        chunk.call_id,
                        partial_transcript,
                        confidence,
                        audio_in_timestamp,
                    )

        except Exception as e:
            logger.error(
                "Error processing audio in ASR",
                extra_fields={
                    "call_id": chunk.call_id,
                    "error": str(e),
                },
            )

    def _should_emit_partial(self) -> bool:
        """Check if partial transcript should be emitted based on interval.

        Returns:
            True if should emit, False otherwise
        """
        now = time.time()

        if self._last_emit_time is None:
            self._last_emit_time = now
            return True

        # Check if enough time has passed (convert ms to seconds)
        elapsed_ms = (now - self._last_emit_time) * 1000

        if elapsed_ms >= self.emit_interval_ms:
            self._last_emit_time = now
            return True

        return False

    async def _emit_partial_transcript(
        self,
        call_id: str,
        transcript: str,
        confidence: float,
        audio_in_timestamp: datetime,
    ) -> None:
        """Emit partial transcript result and measure latency.

        Args:
            call_id: Call session ID
            transcript: Partial transcript text
            confidence: Confidence score
            audio_in_timestamp: Timestamp when audio chunk was received
        """
        from app.schemas.asr import TranscriptResult, TranscriptType

        # Calculate latency: audio_in → partial_transcript
        partial_transcript_timestamp = datetime.now(timezone.utc)
        latency_delta = partial_transcript_timestamp - audio_in_timestamp
        latency_ms = latency_delta.total_seconds() * 1000.0

        # Fail fast if latency exceeds threshold
        if latency_ms > self.latency_threshold_ms:
            logger.error(
                "ASR latency exceeds threshold - failing fast",
                extra_fields={
                    "call_id": call_id,
                    "latency_ms": round(latency_ms, 2),
                    "threshold_ms": self.latency_threshold_ms,
                    "transcript": transcript,
                },
            )
            # Could raise exception here or take other action
            # For now, we log and continue but mark as error

        # Get session and record latency
        session = session_manager.get_session(call_id)
        if session:
            session.record_asr_latency(latency_ms)
            session_manager.update_session(session)

        # Increment transcript count
        self._transcript_count += 1

        # Log latency stats periodically (p50, p95)
        if session and self._transcript_count % self.stats_log_interval == 0:
            stats = session.get_asr_latency_stats()
            if stats.get("count", 0) > 0:
                logger.info(
                    "ASR latency statistics",
                    extra_fields={
                        "call_id": call_id,
                        "count": stats["count"],
                        "p50_ms": round(stats["p50"], 2),
                        "p95_ms": round(stats["p95"], 2),
                        "avg_ms": round(stats["avg"], 2),
                        "min_ms": round(stats["min"], 2),
                        "max_ms": round(stats["max"], 2),
                    },
                )

        result = TranscriptResult(
            transcript=transcript,
            confidence=confidence,
            type=TranscriptType.PARTIAL,
            call_id=call_id,
            timestamp=partial_transcript_timestamp,
            is_final=False,
        )

        # Call callback if provided
        if self.transcript_callback:
            try:
                if asyncio.iscoroutinefunction(self.transcript_callback):
                    asyncio.create_task(self.transcript_callback(result.model_dump()))
                else:
                    self.transcript_callback(result.model_dump())
            except Exception as e:
                logger.error(
                    "Error in transcript callback",
                    extra_fields={"call_id": call_id, "error": str(e)},
                )

        logger.debug(
            "Partial transcript emitted",
            extra_fields={
                "call_id": call_id,
                "transcript": transcript,
                "confidence": confidence,
                "latency_ms": round(latency_ms, 2),
            },
        )

    async def finalize_transcript(self, call_id: str) -> Optional[str]:
        """Finalize and return final transcript.

        Args:
            call_id: Call session ID

        Returns:
            Final transcript or None
        """
        try:
            final_text = await self.asr_backend.finalize()
            if final_text:
                confidence = await self.asr_backend.get_confidence(final_text)

                from datetime import datetime, timezone

                from app.schemas.asr import TranscriptResult, TranscriptType

                result = TranscriptResult(
                    transcript=final_text,
                    confidence=confidence,
                    type=TranscriptType.FINAL,
                    call_id=call_id,
                    timestamp=datetime.now(timezone.utc),
                    is_final=True,
                )

                # Call callback if provided
                if self.transcript_callback:
                    try:
                        if asyncio.iscoroutinefunction(self.transcript_callback):
                            await self.transcript_callback(result.model_dump())
                        else:
                            self.transcript_callback(result.model_dump())
                    except Exception as e:
                        logger.error(
                            "Error in transcript callback",
                            extra_fields={"call_id": call_id, "error": str(e)},
                        )

                logger.info(
                    "Final transcript emitted",
                    extra_fields={
                        "call_id": call_id,
                        "transcript": final_text,
                        "confidence": confidence,
                    },
                )

            return final_text
        except Exception as e:
            logger.error(
                "Error finalizing transcript",
                extra_fields={"call_id": call_id, "error": str(e)},
            )
            return None

    def interrupt(self) -> None:
        """Interrupt ASR processing (e.g., on barge-in)."""
        self._interrupted = True

    async def reset(self) -> None:
        """Reset ASR state."""
        await self.asr_backend.reset()
        self._interrupted = False
        self._chunks_since_emit = 0
        self._last_emit_time = None
        self._transcript_count = 0
