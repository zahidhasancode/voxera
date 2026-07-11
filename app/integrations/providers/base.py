"""Integration provider port — all providers implement this interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.core.enums import (
    IntegrationAuthType,
    IntegrationCategory,
    IntegrationConnectionStatus,
    IntegrationEntityType,
    IntegrationHealthStatus,
    IntegrationProviderSlug,
)


@dataclass(frozen=True)
class ProviderMetadata:
    slug: IntegrationProviderSlug
    name: str
    category: IntegrationCategory
    auth_type: IntegrationAuthType
    description: str
    supported_entities: tuple[IntegrationEntityType, ...]
    oauth_authorize_url: str | None = None
    oauth_token_url: str | None = None
    oauth_revoke_url: str | None = None
    default_scopes: tuple[str, ...] = ()
    webhook_signature_header: str | None = None
    docs_url: str | None = None


@dataclass
class ConnectionContext:
    tenant_id: UUID
    connection_id: UUID
    provider_slug: str
    config: dict[str, Any] = field(default_factory=dict)
    credentials: dict[str, Any] = field(default_factory=dict)
    field_mappings: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


@dataclass
class ProviderHealthResult:
    status: IntegrationHealthStatus
    latency_ms: float | None = None
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderStatusResult:
    status: IntegrationConnectionStatus
    health: IntegrationHealthStatus
    last_sync_at: str | None = None
    message: str | None = None


@dataclass
class SyncFetchResult:
    entity_type: IntegrationEntityType
    records: list[dict[str, Any]]
    next_cursor: str | None = None
    has_more: bool = False


@dataclass
class WebhookProcessResult:
    event_id: str
    event_type: str | None
    entity_type: IntegrationEntityType | None
    records: list[dict[str, Any]] = field(default_factory=list)
    action: str = "upsert"


@dataclass
class ConnectResult:
    status: IntegrationConnectionStatus
    authorization_url: str | None = None
    webhook_url: str | None = None
    message: str | None = None


class IntegrationProvider(ABC):
    """Enterprise integration provider contract."""

    @property
    @abstractmethod
    def metadata(self) -> ProviderMetadata: ...

    async def connect(self, ctx: ConnectionContext, *, redirect_uri: str | None = None) -> ConnectResult:
        raise NotImplementedError

    async def disconnect(self, ctx: ConnectionContext) -> None:
        raise NotImplementedError

    async def health(self, ctx: ConnectionContext) -> ProviderHealthResult:
        raise NotImplementedError

    async def sync(
        self,
        ctx: ConnectionContext,
        *,
        entity_types: list[IntegrationEntityType],
        mode: str,
        cursor: dict[str, str | None] | None = None,
    ) -> list[SyncFetchResult]:
        raise NotImplementedError

    async def webhook(
        self,
        ctx: ConnectionContext,
        *,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> WebhookProcessResult:
        raise NotImplementedError

    async def refresh_token(self, ctx: ConnectionContext) -> dict[str, Any]:
        raise NotImplementedError

    async def validate(self, ctx: ConnectionContext) -> bool:
        raise NotImplementedError

    async def status(self, ctx: ConnectionContext) -> ProviderStatusResult:
        raise NotImplementedError
