"""WebSocket endpoints."""

import asyncio
import json
import uuid
from typing import Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.connection_manager import ConnectionManager
from app.core.logger import get_logger
from app.conversation.events import UserInterrupted, UserTurnCompleted, UserTurnStarted
from app.conversation.state import ConversationState
from app.conversation.turn_manager import TurnManager
from app.llm.llm_consumer import LLMConsumer
from app.llm.streaming_engine import MockStreamingLLMEngine
from app.stt.consumer import STTConsumer
from app.tts import MockStreamingTTSEngine, TTSConsumer
from app.stt.engine import MockSTTEngine
from app.stt.models import TranscriptEvent, TranscriptType
from app.streaming.audio_queue import AudioFrameQueue
from app.streaming.dispatcher import StreamingDispatcher
from app.streaming.metrics import streaming_metrics

router = APIRouter()
logger = get_logger(__name__)

# Use shared connection manager instance
manager = ConnectionManager()


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint with streaming audio pipeline."""
    connected = await manager.connect(websocket)

    if not connected:
        await websocket.close()
        return

    # Initialize conversation state, LLM consumer, and turn manager
    conversation_state = ConversationState()
    llm_engine = MockStreamingLLMEngine(min_token_delay_ms=20.0, max_token_delay_ms=40.0)
    llm_consumer = LLMConsumer(
        engine=llm_engine,
        send_json=websocket.send_json,
        conversation_id=str(conversation_state.conversation_id),
    )
    tts_engine = MockStreamingTTSEngine()
    tts_consumer = TTSConsumer(
        engine=tts_engine,
        send_bytes=websocket.send_bytes,
        send_json=websocket.send_json,
        conversation_id=str(conversation_state.conversation_id),
    )
    turn_manager: Optional[TurnManager] = None

    async def _on_system_turn_start() -> None:
        await tts_consumer.stop()
        conversation_state.start_system_turn()

    async def _on_llm_final(text: str, utterance_id: str) -> None:
        await tts_consumer.start_speaking(text=text, utterance_id=utterance_id)

    async def on_user_turn_started(event: UserTurnStarted) -> None:
        """Handle user turn started; cancel in-flight LLM on new user speech."""
        llm_consumer.cancel()
        logger.info(
            "User turn started (conversation boundary)",
            extra_fields={
                "conversation_id": str(conversation_state.conversation_id),
                "utterance_id": event.utterance_id,
                "turn_count": conversation_state.turn_count,
                "timestamp": event.timestamp.isoformat(),
            },
        )

    async def on_user_turn_completed(event: UserTurnCompleted) -> None:
        """Handle user turn completed; start streaming LLM."""
        logger.info(
            "User turn completed (conversation boundary)",
            extra_fields={
                "conversation_id": str(conversation_state.conversation_id),
                "utterance_id": event.utterance_id,
                "transcript": event.transcript,
                "turn_count": conversation_state.turn_count,
                "timestamp": event.timestamp.isoformat(),
            },
        )
        asyncio.create_task(
            llm_consumer.start_generation(
                transcript=event.transcript,
                utterance_id=event.utterance_id,
                on_system_turn_start=_on_system_turn_start,
                on_system_turn_end=conversation_state.complete_system_turn,
                on_llm_final=_on_llm_final,
            )
        )

    async def on_user_interrupted(_event: UserInterrupted) -> None:
        """Handle barge-in; cancel in-flight LLM and TTS."""
        llm_consumer.cancel()
        await tts_consumer.stop()

    turn_manager = TurnManager(
        state=conversation_state,
        on_user_turn_started=on_user_turn_started,
        on_user_turn_completed=on_user_turn_completed,
        on_user_interrupted=on_user_interrupted,
    )
    logger.info(
        "Conversation turn manager initialized",
        extra_fields={
            "conversation_id": str(conversation_state.conversation_id),
        },
    )

    # Initialize streaming pipeline with singleton metrics
    audio_queue = AudioFrameQueue(max_size=50, metrics=streaming_metrics)
    dispatcher: Optional[StreamingDispatcher] = None
    stt_consumer: Optional[STTConsumer] = None

    async def frame_callback(frame: bytes) -> None:
        """Callback for dispatched audio frames.

        Args:
            frame: Audio frame bytes (20ms PCM16)
        """
        # Placeholder: frame processing will be added in future steps
        # For now, just log that frame was dispatched
        pass

    async def transcript_callback(event: TranscriptEvent) -> None:
        """Callback for STT transcript events.

        Args:
            event: TranscriptEvent to send to client
        """
        try:
            event_dict = event.to_dict()
            await websocket.send_json(event_dict)
            
            # Enhanced logging for transcript events
            if event.type.value == "partial":
                logger.info(
                    "Partial transcript emitted",
                    extra_fields={
                        "type": event.type.value,
                        "utterance_id": event.utterance_id,
                        "transcript": event.transcript,
                        "confidence": round(event.confidence, 3),
                        "timestamp": event.timestamp.isoformat(),
                    },
                )
            else:  # final
                logger.info(
                    "Final transcript emitted",
                    extra_fields={
                        "type": event.type.value,
                        "utterance_id": event.utterance_id,
                        "transcript": event.transcript,
                        "confidence": round(event.confidence, 3),
                        "timestamp": event.timestamp.isoformat(),
                    },
                )

            # Process all transcript events through turn manager
            # This tracks turn boundaries and detects when user turn completes
            if turn_manager:
                await turn_manager.process_transcript_event(event)

        except Exception as e:
            logger.error(
                "Error sending transcript event to client",
                extra_fields={
                    "error": str(e),
                    "event_type": event.type.value if event else "unknown",
                },
                exc_info=True,
            )

    # Initialize STT engine and consumer
    # Configured to emit transcripts more frequently for verification
    stt_engine = MockSTTEngine(
        partial_interval=3,  # Emit partial every 3 frames (~60ms)
        word_probability=0.25,  # Higher probability to generate words
        silence_threshold=15,  # Finalize after 15 frames of silence
    )
    logger.info("Mock STT engine initialized", extra_fields={
        "partial_interval": stt_engine.partial_interval,
        "word_probability": stt_engine.word_probability,
        "silence_threshold": stt_engine.silence_threshold,
    })
    stt_consumer = STTConsumer(
        engine=stt_engine,
        transcript_callback=transcript_callback,
        max_queue_size=50,
    )

    dispatcher = StreamingDispatcher(queue=audio_queue, callback=frame_callback, metrics=streaming_metrics)
    dispatcher.register_stt_consumer(stt_consumer)
    logger.info("STT consumer registered with streaming dispatcher")

    try:
        # Start STT consumer
        await stt_consumer.start()

        # Start dispatcher
        await dispatcher.start()

        # Send welcome message
        await manager.send_personal_message(
            {"type": "connection", "status": "connected"}, websocket
        )

        logger.info(
            "WebSocket connection established with streaming pipeline",
            extra_fields={
                "queue_max_size": audio_queue.max_size,
            },
        )

        # Handle messages and binary frames
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive(), timeout=settings.WEBSOCKET_PING_INTERVAL
                )

                # Handle binary audio frames
                if "bytes" in message:
                    frame = message["bytes"]
                    # Non-blocking enqueue (drop-oldest if full)
                    await audio_queue.enqueue(frame)

                    # Log audio frame received (first few frames and periodically)
                    if audio_queue.frames_enqueued <= 5 or audio_queue.frames_enqueued % 50 == 0:
                        logger.info(
                            "Audio frame received",
                            extra_fields={
                                "frame_size_bytes": len(frame),
                                "frames_enqueued": audio_queue.frames_enqueued,
                                "queue_depth": audio_queue.size(),
                            },
                        )

                    # Log queue stats periodically
                    if audio_queue.frames_enqueued % 100 == 0:
                        stats = audio_queue.get_stats()
                        logger.debug(
                            "Audio queue stats",
                            extra_fields=stats,
                        )

                # Handle text messages
                elif "text" in message:
                    data = message["text"]
                    await handle_message(websocket, data, turn_manager, tts_consumer)

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(
            "WebSocket error",
            extra_fields={"error": str(e)},
            exc_info=True,
        )
    finally:
        # Cancel any in-flight LLM generation and TTS
        llm_consumer.cancel()
        await tts_consumer.stop()
        # Stop STT consumer and dispatcher
        if stt_consumer:
            await stt_consumer.stop()
        if dispatcher:
            await dispatcher.stop()

        # Log final stats
        queue_stats = audio_queue.get_stats()
        dispatcher_stats = dispatcher.get_stats() if dispatcher else {}
        logger.info(
            "WebSocket connection closed",
            extra_fields={
                "queue_stats": queue_stats,
                "dispatcher_stats": dispatcher_stats,
            },
        )

        manager.disconnect(websocket)


async def handle_message(
    websocket: WebSocket,
    message: str,
    turn_manager: Optional[TurnManager] = None,
    tts_consumer: Optional[TTSConsumer] = None,
):
    """Handle incoming WebSocket messages."""
    try:
        data = json.loads(message)
        message_type = data.get("type", "unknown")

        # DEV-ONLY: direct TTS test (bypasses TurnManager)
        if message_type == "dev_test_tts" and tts_consumer:
            text = data.get("text") or "Hello from Voxera TTS test."
            utterance_id = str(uuid.uuid4())
            logger.info(
                "DEV: dev_test_tts injected",
                extra_fields={"text": text, "utterance_id": utterance_id},
            )
            await tts_consumer.start_speaking(text=text, utterance_id=utterance_id)
            return

        # DEV-ONLY: inject fake final transcript to trigger LLM generation (for local testing)
        if message_type == "dev_test_transcript" and turn_manager:
            text = data.get("text") or ""
            utterance_id = str(uuid.uuid4())
            # PARTIAL first so TurnManager starts user turn, then FINAL to complete and trigger LLM
            partial = TranscriptEvent(
                type=TranscriptType.PARTIAL,
                utterance_id=utterance_id,
                transcript=text,
                confidence=1.0,
            )
            await turn_manager.process_transcript_event(partial)
            final = TranscriptEvent(
                type=TranscriptType.FINAL,
                utterance_id=utterance_id,
                transcript=text,
                confidence=1.0,
            )
            await turn_manager.process_transcript_event(final)
            logger.info(
                "DEV: dev_test_transcript injected, LLM generation triggered",
                extra_fields={"text": text, "utterance_id": utterance_id},
            )
            return

        if message_type == "ping":
            await manager.send_personal_message({"type": "pong"}, websocket)
        else:
            logger.debug(f"Received message type: {message_type}")

    except json.JSONDecodeError:
        await manager.send_personal_message(
            {"type": "error", "message": "Invalid JSON format"}, websocket
        )
