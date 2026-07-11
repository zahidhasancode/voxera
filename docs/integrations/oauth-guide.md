# OAuth Guide

## Flow

1. Dashboard calls `POST /integrations/connect` with `redirect_uri`.
2. API returns `authorization_url` for provider OAuth consent.
3. User completes consent; provider redirects to `/api/v1/integrations/oauth/callback?code=&state=`.
4. `IntegrationOAuthManager.exchange_code()` stores encrypted tokens.
5. Connection status becomes `connected`.

## Token lifecycle

- **Refresh** — `IntegrationProvider.refresh_token()` before expiry
- **Rotation** — new credentials row with `rotated_at` timestamp
- **Revocation** — `disconnect()` calls provider revoke URL when configured
- **Expiration** — tracked on `integration_credentials.expires_at`

## State parameter

OAuth state encodes `{tenant_id}:{connection_id}` for secure callback routing.

## Configuration

Store per-connection OAuth app credentials in `connection.config`:

```json
{
  "client_id": "...",
  "client_secret": "...",
  "redirect_uri": "https://app.example.com/api/v1/integrations/oauth/callback"
}
```

Never expose `client_secret` in API responses.
