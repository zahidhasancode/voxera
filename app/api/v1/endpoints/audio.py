"""WebSocket endpoint for real-time audio ingestion."""

import asyncio
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.logger import get_logger, set_call_id
from app.models.call_session import CallSession, CallState
from app.services.audio_output import audio_output_controller
from app.services.audio_pipeline import MetricsConsumer, NullConsumer
from app.services.barge_in import BargeInDetector
from app.services.call_session_manager import session_manager
from app.services.pipeline_manager import pipeline_manager

router = APIRouter()
logger = get_logger(__name__)


class AudioConnection:
    """Represents an audio ingestion WebSocket connection."""

    def __init__(self, websocket: WebSocket, session: CallSession):
        """Initialize audio connection.

        Args:
            websocket: WebSocket connection
            session: Associated CallSession
        """
        self.websocket = websocket
        self.session = session
        self.audio_chunks_received = 0

    async def send_message(self, message: dict) -> None:
        """Send JSON message to client.

        Args:
            message: Message dictionary to send
        """
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(
                "Error sending message to client",
                extra_fields={
                    "call_id": self.session.call_id,
                    "error": str(e),
                },
            )
            raise

    async def send_binary(self, data: bytes) -> None:
        """Send binary data to client.

        Args:
            data: Binary data to send
        """
        try:
            await self.websocket.send_bytes(data)
        except Exception as e:
            logger.error(
                "Error sending binary data to client",
                extra_fields={
                    "call_id": self.session.call_id,
                    "error": str(e),
                },
            )
            raise


class AudioConnectionManager:
    """Manages audio ingestion WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, AudioConnection] = {}

    async def connect(self, websocket: WebSocket, call_id: Optional[str] = None) -> Optional[AudioConnection]:
        """Accept new audio ingestion connection and create CallSession.

        Args:
            websocket: WebSocket connection
            call_id: Optional call ID (generated if not provided)

        Returns:
            AudioConnection if successful, None if max connections reached
        """
        # Check connection limit
        if len(self.active_connections) >= settings.WEBSOCKET_MAX_CONNECTIONS:
            logger.warning(
                "Max audio connections reached",
                extra_fields={"max_connections": settings.WEBSOCKET_MAX_CONNECTIONS},
            )
            return None

        # Create or retrieve CallSession
        if call_id:
            session = session_manager.get_session(call_id)
            if not session:
                session = session_manager.create_session(call_id=call_id)
        else:
            session = session_manager.create_session()

        # Accept WebSocket connection
        await websocket.accept()

        # Create audio connection
        connection = AudioConnection(websocket, session)
        self.active_connections[session.call_id] = connection

        # Set call_id in logger context
        set_call_id(session.call_id)

        # Log call start event
        logger.info(
            "Audio ingestion session started",
            extra_fields={
                "call_id": session.call_id,
                "state": session.state.value,
            },
        )

        # Send connection acknowledgment
        await connection.send_message(
            {
                "type": "connected",
                "call_id": session.call_id,
                "status": "ready",
                "message": "Audio ingestion ready",
            }
        )

        return connection

    def disconnect(self, call_id: str) -> None:
        """Disconnect audio connection and end CallSession.

        Args:
            call_id: Call session ID
        """
        connection = self.active_connections.pop(call_id, None)
        if connection:
            # Transition session to ended state
            if connection.session.is_active():
                connection.session.transition_to(CallState.ENDED)

            # Update session in manager
            session_manager.update_session(connection.session)

            # Log call end event
            duration = connection.session.get_total_duration()
            logger.info(
                "Audio ingestion session ended",
                extra_fields={
                    "call_id": call_id,
                    "audio_chunks_received": connection.audio_chunks_received,
                    "duration": duration,
                },
            )

    def get_connection(self, call_id: str) -> Optional[AudioConnection]:
        """Get connection by call_id.

        Args:
            call_id: Call session ID

        Returns:
            AudioConnection if found, None otherwise
        """
        return self.active_connections.get(call_id)


# Global audio connection manager
audio_manager = AudioConnectionManager()


@router.websocket("/audio")
async def audio_ingestion_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio ingestion.

    Accepts bidirectional connections for:
    - Receiving 20ms PCM audio chunks (binary)
    - Sending audio responses (binary)
    - Control messages (JSON)

    Query Parameters:
        call_id: Optional call ID. If not provided, a new one will be generated.

    Example:
        ws://localhost:8000/api/v1/ws/audio?call_id=abc-123
    """
    connection: Optional[AudioConnection] = None

    try:
        # Extract call_id from query parameters
        call_id = websocket.query_params.get("call_id")

        # Connect and create CallSession
        connection = await audio_manager.connect(websocket, call_id)
        if not connection:
            await websocket.close(code=1008, reason="Max connections reached")
            return

        session = connection.session

        # Transition to listening state
        session.transition_to(CallState.LISTENING)
        session_manager.update_session(session)

        # Create and start audio pipeline
        pipeline = pipeline_manager.create_pipeline(session.call_id)

        # Add default consumers
        metrics_consumer = MetricsConsumer(name="metrics")
        pipeline.add_consumer(metrics_consumer)

        # Add barge-in detector
        barge_in_detector = BargeInDetector(
            name="barge_in",
            energy_threshold=0.01,  # Adjustable threshold
            consecutive_chunks=3,  # 3 consecutive chunks = ~60ms
        )

        # Set callback to stop audio output and notify client on barge-in
        async def handle_barge_in(call_id: str) -> None:
            """Handle barge-in by stopping audio output and notifying client."""
            # Stop audio output
            audio_output_controller.stop_output(call_id)

            # Notify client to stop audio playback
            conn = audio_manager.get_connection(call_id)
            if conn:
                try:
                    await conn.send_message(
                        {
                            "type": "barge_in",
                            "call_id": call_id,
                            "message": "Stop audio output - user speech detected",
                        }
                    )
                except Exception as e:
                    logger.error(
                        "Error notifying client of barge-in",
                        extra_fields={"call_id": call_id, "error": str(e)},
                    )

        barge_in_detector.set_barge_in_callback(handle_barge_in)
        pipeline.add_consumer(barge_in_detector)

        # Start pipeline
        await pipeline.start()

        logger.debug(
            "Audio ingestion ready to receive chunks",
            extra_fields={
                "call_id": session.call_id,
                "state": session.state.value,
                "consumers": pipeline.consumer_count,
            },
        )

        # Main loop: receive audio chunks and messages
        while True:
            try:
                # Receive message with timeout for keepalive
                message = await asyncio.wait_for(
                    websocket.receive(),
                    timeout=settings.WEBSOCKET_PING_INTERVAL,
                )

                # Handle binary audio chunks
                if "bytes" in message:
                    await handle_audio_chunk(connection, message["bytes"])

                # Handle text messages (control/commands)
                elif "text" in message:
                    await handle_text_message(connection, message["text"])

            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await connection.send_message({"type": "ping"})
                except Exception:
                    # Connection may be closed
                    break

    except WebSocketDisconnect:
        # Normal disconnect
        if connection:
            # Cleanup audio output controller
            audio_output_controller.cleanup(connection.session.call_id)
            # Stop pipeline
            await pipeline_manager.remove_pipeline(connection.session.call_id)
            audio_manager.disconnect(connection.session.call_id)
    except Exception as e:
        logger.exception(
            "Error in audio ingestion endpoint",
            extra_fields={
                "call_id": connection.session.call_id if connection else None,
            },
        )
        if connection:
            # Cleanup audio output controller
            audio_output_controller.cleanup(connection.session.call_id)
            # Stop pipeline on error
            await pipeline_manager.remove_pipeline(connection.session.call_id)
            audio_manager.disconnect(connection.session.call_id)
        try:
            await websocket.close(code=1011, reason="Internal error")
        except Exception:
            pass


async def handle_audio_chunk(connection: AudioConnection, audio_data: bytes) -> None:
    """Handle incoming 20ms PCM audio chunk via pipeline.

    Args:
        connection: Audio connection
        audio_data: PCM audio bytes (expected ~20ms chunk)
    """
    connection.audio_chunks_received += 1

    # Ingest into pipeline (non-blocking)
    pipeline = pipeline_manager.get_pipeline(connection.session.call_id)
    if pipeline:
        await pipeline.ingest_chunk(audio_data)
    else:
        logger.warning(
            "Pipeline not found for call",
            extra_fields={"call_id": connection.session.call_id},
        )

    # Log periodically to avoid log spam (every 100 chunks = ~2 seconds)
    if connection.audio_chunks_received % 100 == 0:
        logger.debug(
            "Audio chunk received",
            extra_fields={
                "call_id": connection.session.call_id,
                "chunk_size": len(audio_data),
                "total_chunks": connection.audio_chunks_received,
            },
        )


async def handle_text_message(connection: AudioConnection, text: str) -> None:
    """Handle incoming text message (control/commands).

    Args:
        connection: Audio connection
        text: JSON text message
    """
    import json

    try:
        message = json.loads(text)
        message_type = message.get("type", "unknown")

        if message_type == "ping":
            await connection.send_message({"type": "pong"})
        elif message_type == "state_change":
            # Handle state transition requests
            new_state_str = message.get("state")
            if new_state_str:
                try:
                    new_state = CallState(new_state_str)
                    connection.session.transition_to(new_state)
                    session_manager.update_session(connection.session)

                    # Handle RESPONDING state: prepare for barge-in
                    if new_state == CallState.RESPONDING:
                        # Reset stop event and mark output as active
                        audio_output_controller.reset_stop_event(
                            connection.session.call_id
                        )

                    await connection.send_message(
                        {
                            "type": "state_changed",
                            "state": new_state.value,
                            "call_id": connection.session.call_id,
                        }
                    )
                    logger.info(
                        "Call state changed",
                        extra_fields={
                            "call_id": connection.session.call_id,
                            "state": new_state.value,
                        },
                    )
                except (ValueError, KeyError) as e:
                    await connection.send_message(
                        {
                            "type": "error",
                            "message": f"Invalid state: {str(e)}",
                        }
                    )
        elif message_type == "barge_in_detected":
            # Client-side barge-in detection (alternative to server-side)
            # Stop output and transition to listening
            call_id = connection.session.call_id
            audio_output_controller.stop_output(call_id)
            if connection.session.state == CallState.RESPONDING:
                connection.session.transition_to(CallState.LISTENING)
                session_manager.update_session(connection.session)
                await connection.send_message(
                    {
                        "type": "barge_in_acknowledged",
                        "state": CallState.LISTENING.value,
                    }
                )
        else:
            logger.debug(
                "Unknown message type received",
                extra_fields={
                    "call_id": connection.session.call_id,
                    "message_type": message_type,
                },
            )

    except json.JSONDecodeError:
        logger.warning(
            "Invalid JSON message received",
            extra_fields={"call_id": connection.session.call_id},
        )
        await connection.send_message(
            {"type": "error", "message": "Invalid JSON format"}
        )
