"""WebSocket connection manager."""

from typing import Set

from fastapi import WebSocket

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with optional JWT authentication."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, *, token: str | None = None) -> bool:
        """Accept WebSocket after optional JWT validation."""
        require_auth = settings.is_production or settings.is_staging or token is not None

        if require_auth and settings.database_enabled:
            if not token:
                logger.warning("WebSocket connection rejected: missing token")
                return False
            try:
                from app.database.session import get_db_session
                from app.infrastructure.iam.factory import build_iam_service

                async for session in get_db_session():
                    auth = build_iam_service(session).build_authentication_service()
                    principal = await auth.authenticate_bearer(token)
                    websocket.state.principal = principal
                    break
            except Exception as exc:
                logger.warning("WebSocket authentication failed", extra_fields={"error": str(exc)})
                return False
        elif require_auth and not settings.database_enabled:
            logger.warning("WebSocket connection rejected: database not configured for auth")
            return False

        await websocket.accept()
        self.active_connections.add(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str | dict, websocket: WebSocket):
        """Send a message to a specific client."""
        import json
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str | dict):
        """Broadcast a message to all connected clients."""
        import json
        if isinstance(message, dict):
            message = json.dumps(message)

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    async def disconnect_all(self) -> None:
        """Close all active WebSocket connections during shutdown."""
        connections = list(self.active_connections)
        for connection in connections:
            try:
                await connection.close(code=1001, reason="Server shutting down")
            except Exception as exc:
                logger.warning("Error closing WebSocket", extra_fields={"error": str(exc)})
            finally:
                self.disconnect(connection)
        logger.info("All WebSocket connections closed", extra_fields={"count": len(connections)})


ws_connection_manager = ConnectionManager()
