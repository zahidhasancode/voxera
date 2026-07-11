# Troubleshooting Guide

## API returns 503 "Database is not configured"

Set `DATABASE_URL` and run `alembic upgrade head`.

## Authentication failures (401)

- Verify `JWT_SECRET_KEY` matches between token issuer and API
- Check token expiry
- For API keys: ensure `IAM_ENABLE_API_KEY_AUTH=true` and key is active

## Health ready returns degraded

Check `/api/v1/health/deep` for dependency details:

- Database connectivity
- Knowledge storage path writable
- Embedding/vector provider configuration

## Voice WebSocket disconnects

- Verify WebSocket auth token in production (`ENVIRONMENT=production`)
- Check `VOICE_REQUIRE_PROVIDERS` and provider API keys
- Review `voxera_voice_dropped_frames_total` metric

## Integration OAuth callback fails

- Verify `redirect_uri` matches provider app configuration
- Check `client_id` / `client_secret` in connection config
- Ensure callback URL is reachable: `/api/v1/integrations/oauth/callback`

## Rate limit 429

- Default: 300 req/min per IP, 600 per organization
- Adjust `RATE_LIMIT_*` env vars
- Note: in-process limits are per pod (Redis backing planned)

## Dashboard empty states

| Page | Common cause |
|------|--------------|
| Live Calls | Operations WebSocket backend not implemented |
| Billing | No billing backend yet |
| Analytics | No analytics backend yet |

## Logs

Structured JSON: stdout and `logs/voxera.json`. Filter by `request_id`, `tenant_id`, `correlation_id`.

## Getting help

1. Check [docs/operations/incident-response.md](operations/incident-response.md)
2. Review [docs/release/known-issues.md](release/known-issues.md)
3. Escalate per on-call runbook
