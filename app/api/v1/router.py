"""API v1 router aggregation."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, websocket

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])

# IMPORTANT: WebSocket router MUST be included WITHOUT prefix
api_router.include_router(websocket.router)