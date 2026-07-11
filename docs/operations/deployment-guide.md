# VOXERA Deployment Guide

Production deployment guide for the VOXERA Enterprise Voice Agent Platform.

## Architecture

```
                    ┌─────────────┐
                    │   Ingress   │  TLS, rate limit, WebSocket
                    │   / Nginx   │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ Dashboard  │  │    Web     │  │  API (xN)  │
    │  (nginx)   │  │  (nginx)   │  │  FastAPI   │
    └────────────┘  └────────────┘  └──────┬─────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
             ┌────────────┐          ┌────────────┐          ┌────────────┐
             │ PostgreSQL │          │   Redis    │          │ Prometheus │
             │ + pgvector │          │  (cache)   │          │  Grafana   │
             └────────────┘          └────────────┘          └────────────┘
```

## Quick Start — Docker Compose (Production)

```bash
cp deploy/env/.env.production.example .env.production
# Edit secrets and provider keys

docker compose -f docker-compose.prod.yml up -d --build

# With monitoring
docker compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d
```

Verify:

```bash
curl -f http://localhost/api/v1/health/ready
curl -f http://localhost/api/v1/metrics
```

## Quick Start — Kubernetes (Helm)

```bash
# Create secrets (see deploy/helm/voxera/examples/secrets.md)
kubectl create namespace voxera-prod

helm upgrade --install voxera deploy/helm/voxera \
  -f deploy/helm/voxera/values-production.yaml \
  --namespace voxera-prod
```

## Images

| Image | Dockerfile | Purpose |
|-------|------------|---------|
| `voxera-api` | `Dockerfile` | Production API (multi-stage, non-root) |
| `voxera-api-dev` | `Dockerfile.dev` | Development with hot reload |
| `voxera-dashboard` | `deploy/docker/Dockerfile.dashboard` | Enterprise dashboard static + nginx |
| `voxera-web` | `deploy/docker/Dockerfile.web` | Voice demo static + nginx |

## Health Probes

| Probe | Endpoint | Use |
|-------|----------|-----|
| Liveness | `/api/v1/health/live` | Process alive |
| Readiness | `/api/v1/health/ready` | Accept traffic |
| Startup | `/api/v1/health/ready` | Slow startup (migrations, providers) |
| Metrics | `/api/v1/metrics` | Prometheus scrape |
| Deep | `/api/v1/health/deep` | Diagnostics (not for probes) |

## Rolling Deployments

- **Docker Compose:** `docker compose -f docker-compose.prod.yml up -d --build api`
- **Kubernetes:** RollingUpdate with `maxUnavailable: 0`, `maxSurge: 1`
- **HPA:** CPU/memory autoscaling on API deployment (Helm values)

## Blue/Green & Canary

Helm values support canary weight (`canary.enabled`, `canary.weight`). For full blue/green:

1. Deploy second Helm release (`voxera-green`) with new image tag
2. Switch Ingress service selector or use service mesh traffic split
3. Roll back by reverting Ingress weights

## Scaling Guidelines

| Component | Horizontal scale trigger |
|-----------|-------------------------|
| API | CPU > 65%, p95 latency > 500ms |
| WebSocket | Concurrent connections per pod |
| Workers | Knowledge queue depth (future) |
| Postgres | Read replicas for analytics (future) |

## Related Docs

- [Kubernetes Guide](./kubernetes-guide.md)
- [CI/CD Guide](./cicd-guide.md)
- [Operations Manual](./operations-manual.md)
- [Backup & Restore](./backup-restore.md)
- [Environment Variables](./environment-variables.md)
