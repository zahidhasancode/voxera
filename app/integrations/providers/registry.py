"""Enterprise integration provider registry."""

from __future__ import annotations

from app.core.enums import IntegrationProviderSlug
from app.integrations.providers.base import IntegrationProvider
from app.integrations.providers.catalog import build_provider_catalog


class IntegrationProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, IntegrationProvider] = {}
        for provider in build_provider_catalog():
            self._providers[provider.metadata.slug.value] = provider

    def get(self, slug: str) -> IntegrationProvider:
        provider = self._providers.get(slug)
        if provider is None:
            raise KeyError(f"Unknown integration provider: {slug}")
        return provider

    def list_providers(self) -> list[IntegrationProvider]:
        return list(self._providers.values())

    def list_slugs(self) -> list[str]:
        return list(self._providers.keys())

    def register(self, provider: IntegrationProvider) -> None:
        self._providers[provider.metadata.slug.value] = provider


integration_provider_registry = IntegrationProviderRegistry()
