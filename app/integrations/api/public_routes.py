"""Public integration webhook and OAuth callback routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.v1.dependencies import get_integration_service, map_domain_errors
from app.integrations.schemas.connection import IntegrationConnectionRead
from app.integrations.services.integration_service import IntegrationService

public_router = APIRouter()


@public_router.get("/oauth/callback", response_model=IntegrationConnectionRead)
async def oauth_callback(
    code: str,
    state: str,
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationConnectionRead:
    try:
        return await service.handle_oauth_callback(state=state, code=code)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@public_router.post("/webhooks/{connection_id}", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(
    connection_id: UUID,
    request: Request,
    service: IntegrationService = Depends(get_integration_service),
) -> dict:
    payload = await request.json()
    headers = {k: v for k, v in request.headers.items()}
    try:
        return await service.handle_webhook(
            connection_id=connection_id,
            payload=payload,
            headers=headers,
        )
    except Exception as exc:
        raise map_domain_errors(exc) from exc
