# Provider Development Guide

## Create a provider

1. Subclass `OAuthIntegrationProvider` or `ApiKeyIntegrationProvider`.
2. Implement `metadata` property with `ProviderMetadata`.
3. Override `_fetch_entity()` for provider-specific API pagination.
4. Override `webhook()` for provider-specific event parsing.
5. Register in `build_provider_catalog()` or via `integration_provider_registry.register()`.

## Example

```python
class HubSpotProvider(OAuthIntegrationProvider):
    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            slug=IntegrationProviderSlug.HUBSPOT,
            name="HubSpot",
            category=IntegrationCategory.CRM,
            auth_type=IntegrationAuthType.OAUTH2,
            description="Sync HubSpot contacts and deals",
            supported_entities=(IntegrationEntityType.CUSTOMER, IntegrationEntityType.ORDER),
            oauth_authorize_url="https://app.hubspot.com/oauth/authorize",
            oauth_token_url="https://api.hubapi.com/oauth/v1/token",
            default_scopes=("crm.objects.contacts.read",),
        )

    async def _fetch_entity(self, ctx, entity_type, *, cursor, mode):
        # Provider-specific REST calls using ctx.credentials["access_token"]
        ...
```

## Rules

- No business logic in API routes or service layer beyond orchestration.
- All HTTP calls use timeouts (default 30s).
- Never log credentials.
- Support incremental cursors where the provider API allows.
