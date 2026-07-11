# Pre-production checklist

## Infrastructure

- [ ] `.env.production` populated (no default secrets)
- [ ] Postgres + pgvector deployed with backups enabled
- [ ] Redis deployed (future cache/rate limits)
- [ ] Knowledge PVC / object storage configured
- [ ] TLS certificates on ingress/reverse proxy
- [ ] DNS records for API and dashboard

## Security

- [ ] `JWT_SECRET_KEY`, `API_KEY_SECRET`, `ENCRYPTION_SECRET_KEY` rotated (32+ chars)
- [ ] Container images scanned (Trivy in CI)
- [ ] SBOM archived per release
- [ ] NetworkPolicy applied (K8s)
- [ ] `/api/v1/metrics` restricted to internal network only

## Observability

- [ ] Prometheus scraping `/api/v1/metrics`
- [ ] Grafana dashboards imported
- [ ] Alert rules configured (latency, errors, voice queue)
- [ ] Log aggregation wired (JSON structured logs)
- [ ] On-call rotation documented

## Deployment

- [ ] CI green on main
- [ ] Helm values reviewed for production
- [ ] HPA min/max replicas set for expected load
- [ ] PDB minAvailable ≥ 1
- [ ] Rolling update tested in staging
- [ ] Rollback procedure tested

## Voice & Telephony

- [ ] Voice providers configured and healthy
- [ ] `TWILIO_AUTH_TOKEN` and `TWILIO_PUBLIC_BASE_URL` set
- [ ] WebSocket ingress timeouts ≥ 86400s
- [ ] Sample end-to-end call successful

## DR

- [ ] Postgres backup schedule verified
- [ ] Restore drill completed this quarter
- [ ] Knowledge file backup schedule verified

## Sign-off

| Role | Name | Date |
|------|------|------|
| Platform | | |
| SRE | | |
| Security | | |
