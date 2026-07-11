# Go-Live Checklist — Design Partner Deployment

## T-7 days

- [ ] Staging soak test (24h minimum)
- [ ] Load test smoke profile (`k6 run tests/load/k6-api-load.js`)
- [ ] Secrets rotated and stored in K8s Secret / vault
- [ ] DNS and TLS configured
- [ ] Backup/restore drill completed

## T-1 day

- [ ] Production checklist reviewed ([../operations/production-checklist.md](../operations/production-checklist.md))
- [ ] On-call rotation confirmed
- [ ] Incident response contacts updated
- [ ] Customer-specific tenant and org created
- [ ] IAM users provisioned with appropriate roles

## T-0 (Deploy)

- [ ] CI green on release tag
- [ ] `helm upgrade --install voxera deploy/helm/voxera -f values.production.yaml`
- [ ] `alembic upgrade head`
- [ ] `/api/v1/health/ready` returns healthy
- [ ] Dashboard accessible and login works
- [ ] Smoke test: create agent, upload knowledge, test voice WebSocket

## T+1 hour

- [ ] Monitor error rate, latency, voice queue depth
- [ ] Review structured logs for anomalies
- [ ] Confirm no CRITICAL alerts firing

## T+24 hours

- [ ] Customer sign-off on acceptance criteria
- [ ] Post-deploy review scheduled

## Rollback trigger

- Error rate >5% sustained 10 minutes
- P95 API latency >2× baseline
- Data integrity issue confirmed
- Security incident

Procedure: [release-checklist.md](release-checklist.md#rollback)
