# VOXERA Reliability Runbook

Operational runbook for on-call engineers. See also [operations-manual.md](./operations-manual.md) and [incident-response.md](./incident-response.md).

## Startup sequence

1. Postgres + Redis healthy
2. API migrations (`RUN_MIGRATIONS=true`)
3. Config validation (`scripts/validate-env.py`)
4. Readiness probe `/api/v1/health/ready` → 200
5. Frontends + nginx
6. Prometheus scrape `/api/v1/metrics`

## Health endpoints

| Endpoint | Use |
|----------|-----|
| `GET /api/v1/health/live` | Liveness — process up |
| `GET /api/v1/health/ready` | Readiness — DB, storage, providers |
| `GET /api/v1/health/deep` | Diagnostics + platform metrics snapshot |
| `GET /api/v1/metrics` | Prometheus scrape (restrict to internal network) |

## Rolling deploy

**Docker Compose:**
```bash
docker compose -f docker-compose.prod.yml up -d --build api worker
```

**Kubernetes / Helm:**
```bash
helm upgrade voxera deploy/helm/voxera -f deploy/helm/voxera/values-production.yaml \
  --set api.image.tag=<sha> --namespace voxera-prod
```

## Canary deploy

Enable in Helm values:
```yaml
canary:
  enabled: true
  weight: 10
```

Monitor error rate and latency for 15 minutes before increasing weight.

## Rollback

```bash
helm rollback voxera --namespace voxera-prod
kubectl rollout undo deployment/voxera-api
```

## Common alerts

| Alert | Action |
|-------|--------|
| VoxeraHighErrorRate | Check logs, recent deploy, provider status |
| VoxeraHighLatencyP95 | Scale HPA, check voice queue depth |
| VoxeraVoiceQueueBacklog | Scale API + worker replicas |
| VoxeraTargetDown | Check pod status, ingress, DB connectivity |

## Observability URLs (compose monitoring)

| Service | URL |
|---------|-----|
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| Jaeger | http://localhost:16686 |

## Backup

Daily Postgres backup:
```bash
./deploy/scripts/backup-postgres.sh
```

See [backup-restore.md](./backup-restore.md).
