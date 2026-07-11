# Enterprise Security Architecture

This document describes the HTTP authentication and authorization layer wired in the security hardening sprint.

## Overview

VOXERA uses **JWT sessions** for human users and **HMAC API keys** for machine clients. All `/api/v1/*` routes are protected except explicit public endpoints. Tenant isolation is enforced at the middleware boundary using organization ↔ tenant mapping.

## Secret keys

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET_KEY` | HS256 signing for access and refresh tokens |
| `API_KEY_SECRET` | HMAC hashing for API key verification |
| `ENCRYPTION_SECRET_KEY` | Field-level encryption (`LocalSecretProvider`) |
| `SECRET_KEY` | **Development-only** fallback when dedicated keys are unset |

In **staging** and **production**, all three dedicated keys are required at startup when `DATABASE_URL` is configured. The application fails fast if keys are missing or use the insecure default.

## Public endpoints

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/v1/iam/auth/login` | Email/password login |
| POST | `/api/v1/iam/auth/register` | Organization + owner signup |
| POST | `/api/v1/iam/auth/refresh` | Refresh token rotation |
| GET | `/api/v1/health` | Liveness |
| GET | `/docs`, `/redoc`, `/openapi.json` | Development only (`DEBUG=true`) |

## Authentication methods

### Bearer JWT

```
Authorization: Bearer <access_token>
```

Access tokens include claims: `sub`, `org`, `role`, `permissions`, `type=access`.

Each login creates a server-side session row. Requests are rejected when:

- JWT signature or expiry is invalid
- Session is revoked or expired
- User account is not `active`
- User is not a member of the token organization

### API key

```
X-Api-Key: vx_...
```

API keys map to an organization and optional explicit permission list. Revoked or expired keys are rejected.

## Authorization

### Middleware (`AuthenticationMiddleware`)

1. Authenticates every protected HTTP request
2. Validates `/api/v1/tenants/{tenant_id}/...` against the caller's organization tenant
3. Validates `/api/v1/iam/organizations/{org_id}/...` against the caller's organization
4. Requires `manage_organization` for `/api/v1/tenants` collection routes

### FastAPI dependencies (`app/iam/api/deps.py`)

| Dependency | Purpose |
|------------|---------|
| `get_current_principal` | JWT or API key identity |
| `get_current_user` | JWT user session only |
| `get_tenant_context` | Tenant-scoped enterprise handler context |
| `require_permissions(...)` | RBAC gate for IAM routes |

## IAM HTTP endpoints

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/iam/auth/logout` | Bearer JWT |
| GET | `/api/v1/iam/auth/me` | Bearer JWT |

`X-Actor-Id` has been **removed**. Actor identity is derived from JWT claims.

## WebSocket authentication

Voice WebSocket (`WS /api/v1/?token=<access_token>`):

- **Production/staging**: JWT required via query parameter
- **Development**: Optional when database is disabled; required when token is supplied

## Twilio signature validation

`POST /twilio/inbound` validates `X-Twilio-Signature` when `TWILIO_AUTH_TOKEN` is set. In production/staging, missing configuration returns `503`.

## Migration steps

1. Generate three 32+ character secrets:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
2. Set `JWT_SECRET_KEY`, `API_KEY_SECRET`, `ENCRYPTION_SECRET_KEY` in your environment
3. Set `TWILIO_AUTH_TOKEN` for telephony deployments
4. Restart the API — startup validation runs in the lifespan hook
5. Bootstrap first tenant via `POST /api/v1/iam/auth/register`
6. Use returned `access_token` for all subsequent API calls
7. Rotate API keys issued before the secret split (hashes use `API_KEY_SECRET`)

## Testing

```bash
pytest tests/iam/test_authentication_service.py \
       tests/iam/test_auth_middleware.py \
       tests/iam/test_security_config.py \
       tests/iam/test_twilio_validation.py \
       tests/iam/test_rbac_http.py -q
```
