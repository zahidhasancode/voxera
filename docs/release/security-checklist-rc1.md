# RC1 Security Checklist

## Authentication & Authorization

- [x] JWT authentication middleware on `/api/v1/*`
- [x] API key authentication supported
- [x] Tenant path validation in middleware
- [x] Organization path validation in middleware
- [x] RBAC engine implemented
- [ ] **Per-route RBAC on all tenant REST endpoints** (GA blocker)
- [x] Production secret validation (`validate_security_settings`)
- [x] Passwords bcrypt-hashed; API keys HMAC-stored
- [x] Integration credentials encrypted at rest

## Network & Infrastructure

- [x] Docker non-root user (uid 10001)
- [x] Helm NetworkPolicy template
- [x] TLS via ingress (customer-configured)
- [ ] `/api/v1/metrics` restricted to internal network
- [ ] Redis auth enabled (when Redis deployed)
- [x] Webhook signature validation framework

## Application Security

- [x] Rate limiting (IP, endpoint, org, tenant, API key)
- [x] Request timeout middleware
- [x] Structured error responses (no stack traces in prod)
- [x] Document upload validation (path traversal, XSS patterns)
- [x] Prompt injection test suite (intent engine resilience)
- [x] Tenant isolation security tests

## CI/CD Security

- [x] ruff + black lint
- [x] pip-audit (non-blocking — manual review required)
- [x] Trivy FS + image scan (non-blocking — manual review required)
- [x] SBOM generation
- [ ] CodeQL / Semgrep SAST
- [ ] npm audit for dashboard/web

## Compliance Readiness

- [x] Audit log for IAM and integration actions
- [x] Verifier compliance engine
- [x] GDPR/HIPAA/SOC2 framework enums
- [ ] Formal compliance audit (post-GA)

## RC1 Verdict

**Conditional pass** — acceptable for design partners with network isolation and documented compensating controls for RC1-001 (RBAC gap).
