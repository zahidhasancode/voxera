"""API v1 router aggregation."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, metrics, websocket
from app.api.v1.enterprise_router import enterprise_router
from app.iam.api.routes import auth_router, org_router
from app.integrations.api.public_routes import public_router as integrations_public_router

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

# Enterprise IAM (auth + organizations, users, roles, API keys)
api_router.include_router(auth_router, prefix="/iam/auth", tags=["iam-auth"])
api_router.include_router(org_router, prefix="/iam", tags=["iam"])

# Enterprise multi-tenant REST APIs (Sprint 1 — does not affect voice WebSocket)
api_router.include_router(enterprise_router)

# Integration OAuth callbacks and inbound webhooks (public)
api_router.include_router(integrations_public_router, prefix="/integrations", tags=["integrations-public"])

# IMPORTANT: WebSocket router MUST be included WITHOUT prefix
api_router.include_router(websocket.router)