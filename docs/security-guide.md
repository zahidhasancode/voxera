# Security Guide

Enterprise security practices for VOXERA deployments.

## Authentication

- JWT access tokens (HS256) with configurable expiry
- API keys (HMAC-SHA256 hash stored; full key shown once)
- MFA hooks via IAM (factor enrollment supported)

## Authorization

- RBAC engine with permission catalog (`IamPermission`)
- Middleware: tenant and organization path validation
- **RC1 note:** Per-route RBAC on tenant REST endpoints planned for GA

## Encryption

- Passwords: bcrypt
- Field-level secrets: `LocalSecretProvider` (XOR stream keyed from `ENCRYPTION_SECRET_KEY`)
- Integration credentials: encrypted at rest
- TLS: required at ingress (customer-managed)

## Tenant isolation

- All enterprise resources scoped by `tenant_id`
- Middleware validates org owns tenant on tenant paths
- Cross-tenant security tests in `tests/security/`

## Rate limiting

- Pre-auth: IP and endpoint limits
- Post-auth: organization, tenant, API key limits
- RC1: in-process (per-pod); Redis planned for GA

## Secrets management

Production requires (minimum 32 characters each):

- `JWT_SECRET_KEY`
- `API_KEY_SECRET`
- `ENCRYPTION_SECRET_KEY`

`validate_security_settings()` rejects insecure defaults in staging/production.

## Container security

- Non-root Docker user (uid 10001)
- Helm NetworkPolicy template
- Trivy scanning in CI (manual review for RC1)

## Security testing

```bash
pytest tests/security/ -m security -v
./scripts/run-qa-suite.sh pr  # includes security suite
```

## Incident response

See [operations/incident-response.md](operations/incident-response.md).

## RC1 checklist

See [release/security-checklist-rc1.md](release/security-checklist-rc1.md).
