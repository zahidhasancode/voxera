# Kubernetes Guide

## Prerequisites

- Kubernetes 1.28+
- Helm 3.12+
- Ingress controller (nginx recommended)
- StorageClass supporting ReadWriteMany (for knowledge PVC) or use object storage
- cert-manager (optional, for TLS)

## Install

```bash
kubectl create namespace voxera-prod

# Secrets — never commit real values
kubectl create secret generic voxera-api-secrets \
  --namespace voxera-prod \
  --from-literal=JWT_SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=API_KEY_SECRET="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=DATABASE_URL="postgresql+asyncpg://..."

helm upgrade --install voxera deploy/helm/voxera \
  --namespace voxera-prod \
  -f deploy/helm/voxera/values-production.yaml \
  --set api.image.tag=0.1.0
```

## Resources Created

| Resource | Purpose |
|----------|---------|
| Deployment (api) | FastAPI with rolling updates |
| Deployment (dashboard) | Static dashboard |
| Service | ClusterIP for api + dashboard |
| Ingress | TLS, routing, WebSocket timeouts |
| HPA | CPU/memory autoscaling |
| PDB | minAvailable during node drains |
| NetworkPolicy | Restrict api ingress/egress |
| PVC | Knowledge file storage |
| ServiceMonitor | Prometheus Operator scrape |
| ConfigMap | Non-secret environment config |

## Probes

Configured in `values.yaml`:

```yaml
api:
  livenessProbe:
    path: /api/v1/health/live
  readinessProbe:
    path: /api/v1/health/ready
  startupProbe:
    path: /api/v1/health/ready
    failureThreshold: 30
```

## WebSocket

Ingress annotations enable long-lived connections:

```yaml
nginx.ingress.kubernetes.io/proxy-read-timeout: "86400"
nginx.ingress.kubernetes.io/proxy-send-timeout: "86400"
```

## Zero-Downtime Deploy

1. HPA maintains minimum replicas ≥ 2
2. PDB ensures at least 1 pod during voluntary disruption
3. RollingUpdate with `maxUnavailable: 0`
4. Readiness probe gates traffic until DB/providers healthy

## Multi-Region (Future)

- Deploy independent Helm releases per region
- Global load balancer with geo routing
- Postgres read replicas + cross-region backup (see backup-restore.md)
