"""OAuth token lifecycle for integrations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx

from app.integrations.providers.base import ConnectionContext
from app.integrations.providers.registry import integration_provider_registry


class IntegrationOAuthManager:
    async def build_authorization_url(
        self,
        *,
        provider_slug: str,
        ctx: ConnectionContext,
        redirect_uri: str,
    ) -> str:
        provider = integration_provider_registry.get(provider_slug)
        result = await provider.connect(ctx, redirect_uri=redirect_uri)
        if not result.authorization_url:
            raise ValueError("Provider did not return authorization URL")
        return result.authorization_url

    async def exchange_code(
        self,
        *,
        token_url: str,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )
            response.raise_for_status()
            return response.json()

    async def refresh(
        self,
        *,
        provider_slug: str,
        ctx: ConnectionContext,
    ) -> dict[str, Any]:
        provider = integration_provider_registry.get(provider_slug)
        return await provider.refresh_token(ctx)

    @staticmethod
    def compute_expiry(token_response: dict[str, Any]) -> datetime | None:
        expires_in = token_response.get("expires_in")
        if expires_in is None:
            return None
        return datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))


integration_oauth_manager = IntegrationOAuthManager()
