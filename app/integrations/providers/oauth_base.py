"""OAuth2-capable integration provider base."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.enums import (
    IntegrationConnectionStatus,
    IntegrationEntityType,
    IntegrationHealthStatus,
)
from app.integrations.providers.base import (
    ConnectResult,
    ConnectionContext,
    IntegrationProvider,
    ProviderHealthResult,
    ProviderStatusResult,
    SyncFetchResult,
    WebhookProcessResult,
)


class OAuthIntegrationProvider(IntegrationProvider):
    """Base for OAuth2 providers with token refresh and revocation."""

    async def connect(self, ctx: ConnectionContext, *, redirect_uri: str | None = None) -> ConnectResult:
        meta = self.metadata
        if not redirect_uri or not meta.oauth_authorize_url:
            return ConnectResult(
                status=IntegrationConnectionStatus.ERROR,
                message="OAuth redirect URI and authorize URL required",
            )
        state = f"{ctx.tenant_id}:{ctx.connection_id}"
        params = {
            "client_id": ctx.config.get("client_id", ""),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": " ".join(meta.default_scopes),
        }
        url = f"{meta.oauth_authorize_url}?{urlencode(params)}"
        return ConnectResult(
            status=IntegrationConnectionStatus.CONNECTING,
            authorization_url=url,
        )

    async def refresh_token(self, ctx: ConnectionContext) -> dict[str, Any]:
        meta = self.metadata
        refresh = ctx.credentials.get("refresh_token")
        if not refresh or not meta.oauth_token_url:
            raise ValueError("Refresh token or token URL not configured")
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                meta.oauth_token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh,
                    "client_id": ctx.config.get("client_id", ""),
                    "client_secret": ctx.config.get("client_secret", ""),
                },
            )
            response.raise_for_status()
            data = response.json()
        data["_refresh_latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        return data

    async def disconnect(self, ctx: ConnectionContext) -> None:
        meta = self.metadata
        token = ctx.credentials.get("access_token")
        if token and meta.oauth_revoke_url:
            async with httpx.AsyncClient(timeout=15.0) as client:
                await client.post(
                    meta.oauth_revoke_url,
                    data={"token": token},
                    auth=(
                        ctx.config.get("client_id", ""),
                        ctx.config.get("client_secret", ""),
                    ),
                )

    async def health(self, ctx: ConnectionContext) -> ProviderHealthResult:
        if not ctx.credentials.get("access_token"):
            return ProviderHealthResult(
                status=IntegrationHealthStatus.UNHEALTHY,
                message="No access token",
            )
        return ProviderHealthResult(status=IntegrationHealthStatus.HEALTHY, latency_ms=0.0)

    async def validate(self, ctx: ConnectionContext) -> bool:
        return bool(ctx.config.get("client_id")) and bool(ctx.credentials.get("access_token"))

    async def status(self, ctx: ConnectionContext) -> ProviderStatusResult:
        health = await self.health(ctx)
        return ProviderStatusResult(
            status=IntegrationConnectionStatus.CONNECTED
            if health.status == IntegrationHealthStatus.HEALTHY
            else IntegrationConnectionStatus.ERROR,
            health=health.status,
            message=health.message,
        )

    async def webhook(
        self,
        ctx: ConnectionContext,
        *,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> WebhookProcessResult:
        event_id = str(payload.get("id") or payload.get("event_id") or headers.get("x-request-id", ""))
        event_type = payload.get("type") or payload.get("event")
        return WebhookProcessResult(
            event_id=event_id or "unknown",
            event_type=str(event_type) if event_type else None,
            records=[payload],
        )

    async def sync(
        self,
        ctx: ConnectionContext,
        *,
        entity_types: list[IntegrationEntityType],
        mode: str,
        cursor: dict[str, str | None] | None = None,
    ) -> list[SyncFetchResult]:
        results: list[SyncFetchResult] = []
        for entity in entity_types:
            if entity not in self.metadata.supported_entities:
                continue
            fetched = await self._fetch_entity(ctx, entity, cursor=cursor, mode=mode)
            results.append(fetched)
        return results

    async def _fetch_entity(
        self,
        ctx: ConnectionContext,
        entity_type: IntegrationEntityType,
        *,
        cursor: dict[str, str | None] | None,
        mode: str,
    ) -> SyncFetchResult:
        """Override in concrete providers for provider-specific API calls."""
        return SyncFetchResult(entity_type=entity_type, records=[], has_more=False)


class ApiKeyIntegrationProvider(IntegrationProvider):
    """Base for API-key authenticated providers."""

    async def connect(self, ctx: ConnectionContext, *, redirect_uri: str | None = None) -> ConnectResult:
        if not ctx.credentials.get("api_key"):
            return ConnectResult(
                status=IntegrationConnectionStatus.PENDING,
                message="API key required",
            )
        valid = await self.validate(ctx)
        status = IntegrationConnectionStatus.CONNECTED if valid else IntegrationConnectionStatus.ERROR
        return ConnectResult(status=status)

    async def refresh_token(self, ctx: ConnectionContext) -> dict[str, Any]:
        return ctx.credentials

    async def disconnect(self, ctx: ConnectionContext) -> None:
        return None

    async def health(self, ctx: ConnectionContext) -> ProviderHealthResult:
        if not ctx.credentials.get("api_key"):
            return ProviderHealthResult(status=IntegrationHealthStatus.UNHEALTHY, message="Missing API key")
        return ProviderHealthResult(status=IntegrationHealthStatus.HEALTHY)

    async def validate(self, ctx: ConnectionContext) -> bool:
        return bool(ctx.credentials.get("api_key"))

    async def status(self, ctx: ConnectionContext) -> ProviderStatusResult:
        health = await self.health(ctx)
        return ProviderStatusResult(
            status=IntegrationConnectionStatus.CONNECTED
            if health.status == IntegrationHealthStatus.HEALTHY
            else IntegrationConnectionStatus.ERROR,
            health=health.status,
            message=health.message,
        )

    async def sync(
        self,
        ctx: ConnectionContext,
        *,
        entity_types: list[IntegrationEntityType],
        mode: str,
        cursor: dict[str, str | None] | None = None,
    ) -> list[SyncFetchResult]:
        return [
            SyncFetchResult(entity_type=e, records=[])
            for e in entity_types
            if e in self.metadata.supported_entities
        ]

    async def webhook(
        self,
        ctx: ConnectionContext,
        *,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> WebhookProcessResult:
        event_id = str(payload.get("id") or payload.get("event_id") or headers.get("x-request-id", ""))
        event_type = payload.get("type") or payload.get("event")
        return WebhookProcessResult(
            event_id=event_id or "unknown",
            event_type=str(event_type) if event_type else None,
            records=[payload],
        )
