"""WebSocket endpoint for the browser voice pipeline."""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.connection_manager import ws_connection_manager
from app.core.logger import get_logger
from app.stt.consumer import STTConsumer
from app.stt.engine import StreamingSTTEngine
from app.stt.models import TranscriptEvent
from app.streaming.audio_queue import AudioFrameQueue
from app.streaming.dispatcher import StreamingDispatcher
from app.streaming.metrics import streaming_metrics
from app.voice.factory import build_llm_engine, build_stt_engine, build_tts_engine, describe_voice_providers
from app.voice.session import VoiceSession

router = APIRouter()
logger = get_logger(__name__)

# The shared instance, so graceful shutdown also closes voice connections.
manager = ws_connection_manager


async def _noop_frame_callback(_frame: bytes) -> None:
    """The dispatcher fans frames out to the STT consumer; nothing else listens yet."""


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, token: str | None = Query(default=None)):
    """Voice WebSocket: PCM16 audio in, transcripts, LLM tokens and speech out.

    Client → server: binary PCM16 mono frames (VOICE_SAMPLE_RATE, 20 ms each);
    JSON {"type": "ping"}. Server → client: see docs/voice-protocol.md.
    """
    connected = await manager.connect(websocket, token=token)
    if not connected:
        await websocket.close()
        return

    session: Optional[VoiceSession] = None
    stt_engine: Optional[StreamingSTTEngine] = None
    stt_consumer: Optional[STTConsumer] = None
    dispatcher: Optional[StreamingDispatcher] = None
    audio_queue = AudioFrameQueue(max_size=50, metrics=streaming_metrics)

    try:
        # Building the engines can fail (provider not configured, bad key). Do it inside
        # the try so the client gets a reason and the connection is always released.
        try:
            session = VoiceSession(
                llm_engine=build_llm_engine(),
                tts_engine=build_tts_engine(),
                send_json=websocket.send_json,
                send_bytes=websocket.send_bytes,
            )
            stt_engine = build_stt_engine()
        except ValueError as exc:
            logger.warning("Voice providers unavailable", extra_fields={"error": str(exc)})
            await websocket.send_json({
                "type": "error",
                "code": "voice_providers_unavailable",
                "message": str(exc),
            })
            await websocket.close(code=1011)
            return

        async def transcript_callback(event: TranscriptEvent) -> None:
            """Send each STT event to the client and into turn-taking."""
            try:
                await websocket.send_json(event.to_dict())
                await session.process_transcript_event(event)
            except Exception as e:
                logger.error(
                    "Error handling transcript event",
                    extra_fields={"error": str(e), "event_type": event.type.value},
                    exc_info=True,
                )

        stt_consumer = STTConsumer(engine=stt_engine, transcript_callback=transcript_callback, max_queue_size=50)
        dispatcher = StreamingDispatcher(queue=audio_queue, callback=_noop_frame_callback, metrics=streaming_metrics)
        dispatcher.register_stt_consumer(stt_consumer)
        await stt_consumer.start()
        await dispatcher.start()

        providers = describe_voice_providers()
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "conversation_id": session.conversation_id,
            "providers": providers,
            "audio": {
                "sample_rate": settings.VOICE_SAMPLE_RATE,
                "frame_ms": settings.VOICE_FRAME_MS,
                "encoding": "pcm_s16le",
            },
        })
        logger.info(
            "Voice WebSocket connected",
            extra_fields={"conversation_id": session.conversation_id, "providers": providers},
        )

        while True:
            try:
                message = await asyncio.wait_for(websocket.receive(), timeout=settings.WEBSOCKET_PING_INTERVAL)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
                continue

            if message.get("type") == "websocket.disconnect":
                break
            frame = message.get("bytes")
            if frame is not None:
                # Non-blocking enqueue (drop-oldest if full)
                await audio_queue.enqueue(frame)
                if audio_queue.frames_enqueued % 500 == 0:
                    logger.debug("Audio queue stats", extra_fields=audio_queue.get_stats())
                continue
            text = message.get("text")
            if text is not None:
                await handle_message(websocket, text, session)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error("WebSocket error", extra_fields={"error": str(e)}, exc_info=True)
    finally:
        if session is not None:
            await session.close()
        if stt_consumer is not None:
            await stt_consumer.stop()
        if stt_engine is not None:
            await stt_engine.close()
        if dispatcher is not None:
            await dispatcher.stop()
        logger.info(
            "WebSocket connection closed",
            extra_fields={
                "queue_stats": audio_queue.get_stats(),
                "dispatcher_stats": dispatcher.get_stats() if dispatcher else {},
            },
        )
        manager.disconnect(websocket)


async def handle_message(websocket: WebSocket, message: str, session: Optional[VoiceSession] = None) -> None:
    """Handle incoming JSON messages."""
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        await manager.send_personal_message({"type": "error", "message": "Invalid JSON format"}, websocket)
        return
    if not isinstance(data, dict):
        await manager.send_personal_message({"type": "error", "message": "Invalid message"}, websocket)
        return

    message_type = data.get("type", "unknown")

    if message_type == "ping":
        await manager.send_personal_message({"type": "pong"}, websocket)
        return

    if message_type in ("dev_test_tts", "dev_test_transcript"):
        # These let a client make the server call the LLM and TTS providers with any
        # text, so they exist in development only.
        if not settings.voice_dev_messages_enabled or session is None:
            await manager.send_personal_message(
                {"type": "error", "code": "dev_message_disabled", "message": "Not available in this environment"},
                websocket,
            )
            return
        text = str(data.get("text") or "")[:2000]
        if message_type == "dev_test_tts":
            await session.speak_text(text or "Hello from Voxera TTS test.")
        elif text.strip():
            await session.inject_transcript(text)
        return

    logger.debug(f"Received message type: {message_type}")
