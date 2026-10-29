"""API v1 router aggregation."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, metrics, websocket
from app.iam.api.routes import auth_router, org_router

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

# Enterprise IAM (auth + organizations, users, roles, API keys)
api_router.include_router(auth_router, prefix="/iam/auth", tags=["iam-auth"])
api_router.include_router(org_router, prefix="/iam", tags=["iam"])

# IMPORTANT: WebSocket router MUST be included WITHOUT prefix
api_router.include_router(websocket.router)