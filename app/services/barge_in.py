"""Barge-in detection for interrupting system responses."""

import asyncio
from typing import Awaitable, Callable, Optional, Union

from app.core.logger import get_logger
from app.models.call_session import CallState
from app.services.audio_pipeline import AudioChunk, AudioConsumer
from app.services.call_session_manager import session_manager

logger = get_logger(__name__)


class BargeInDetector(AudioConsumer):
    """Detects user speech during system response (barge-in)."""

    def __init__(
        self,
        name: str = "barge_in",
        max_queue_size: int = 50,
        energy_threshold: float = 0.01,
        consecutive_chunks: int = 3,
    ):
        """Initialize barge-in detector.

        Args:
            name: Consumer name
            max_queue_size: Maximum queue size
            energy_threshold: Energy threshold for speech detection (0.0-1.0)
            consecutive_chunks: Number of consecutive chunks with speech to trigger barge-in
        """
        super().__init__(name, max_queue_size)
        self.energy_threshold = energy_threshold
        self.consecutive_chunks = consecutive_chunks
        self.speech_chunk_count = 0
        self.barge_in_callback: Optional[
            Union[Callable[[str], None], Callable[[str], Awaitable[None]]]
        ] = None

    def set_barge_in_callback(
        self,
        callback: Union[Callable[[str], None], Callable[[str], Awaitable[None]]],
    ) -> None:
        """Set callback to be called when barge-in is detected.

        Args:
            callback: Callback function (sync or async) that takes call_id as argument
        """
        self.barge_in_callback = callback

    async def process_chunk(self, chunk: AudioChunk) -> None:
        """Process audio chunk for barge-in detection.

        Args:
            chunk: Audio chunk to analyze
        """
        # Get session to check current state
        session = session_manager.get_session(chunk.call_id)
        if not session:
            return

        # Only detect barge-in when in RESPONDING state
        if session.state != CallState.RESPONDING:
            self.speech_chunk_count = 0
            return

        # Simple energy-based speech detection
        # Calculate RMS (Root Mean Square) energy
        if self._has_speech(chunk.data):
            self.speech_chunk_count += 1

            # Trigger barge-in if consecutive speech chunks detected
            if self.speech_chunk_count >= self.consecutive_chunks:
                await self._trigger_barge_in(chunk.call_id)
                self.speech_chunk_count = 0
        else:
            # Reset counter if no speech detected
            self.speech_chunk_count = 0

    def _has_speech(self, audio_data: bytes) -> bool:
        """Detect if audio chunk contains speech.

        Simple energy-based VAD (Voice Activity Detection).
        In production, this could be replaced with ML-based VAD.

        Args:
            audio_data: PCM audio bytes

        Returns:
            True if speech detected, False otherwise
        """
        if len(audio_data) < 2:
            return False

        # Convert bytes to audio samples (assuming 16-bit PCM)
        import struct

        # Convert to signed 16-bit integers
        samples = struct.unpack(f"<{len(audio_data) // 2}h", audio_data)

        # Calculate RMS energy
        if not samples:
            return False

        # Normalize samples to [-1, 1]
        normalized = [s / 32768.0 for s in samples]

        # Calculate RMS
        rms = (sum(s * s for s in normalized) / len(normalized)) ** 0.5

        return rms > self.energy_threshold

    async def _trigger_barge_in(self, call_id: str) -> None:
        """Trigger barge-in event.

        Args:
            call_id: Call session ID
        """
        session = session_manager.get_session(call_id)
        if not session or session.state != CallState.RESPONDING:
            return

        logger.info(
            "Barge-in detected",
            extra_fields={
                "call_id": call_id,
                "previous_state": session.state.value,
            },
        )

        # Transition to listening state
        try:
            session.transition_to(CallState.LISTENING)
            session_manager.update_session(session)

            # Call callback to stop audio output (non-blocking)
            if self.barge_in_callback:
                try:
                    # Always call in a task to ensure non-blocking
                    if asyncio.iscoroutinefunction(self.barge_in_callback):
                        asyncio.create_task(self.barge_in_callback(call_id))
                    else:
                        # Wrap sync callback in task to avoid blocking
                        async def call_sync():
                            self.barge_in_callback(call_id)  # type: ignore

                        asyncio.create_task(call_sync())
                except Exception as e:
                    logger.error(
                        "Error in barge-in callback",
                        extra_fields={"call_id": call_id, "error": str(e)},
                    )

            logger.info(
                "Barge-in handled: transitioned to listening",
                extra_fields={
                    "call_id": call_id,
                    "new_state": session.state.value,
                },
            )
        except ValueError as e:
            logger.warning(
                "Invalid state transition for barge-in",
                extra_fields={"call_id": call_id, "error": str(e)},
            )
