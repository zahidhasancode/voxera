# Kubernetes Manifests

Production deployments should use the **Helm chart** in `deploy/helm/voxera/`.

```bash
helm upgrade --install voxera deploy/helm/voxera \
  -f deploy/helm/voxera/values-production.yaml \
  --namespace voxera-prod --create-namespace
```

## Resources included in Helm chart

| Kind | File | Purpose |
|------|------|---------|
| Deployment | `deployment-api.yaml` | API with rolling updates |
| Deployment | `deployment-worker.yaml` | Horizontally scaled worker tier |
| Deployment | `deployment-dashboard.yaml` | Enterprise dashboard |
| Service | `service-api.yaml`, `service-dashboard.yaml` | ClusterIP |
| Service | `service-canary.yaml` | Canary traffic split |
| Ingress | `ingress.yaml` | TLS + WebSocket |
| Ingress | `ingress-canary.yaml` | NGINX canary weight |
| ConfigMap | `configmap-api.yaml` | Non-secret config |
| HPA | `hpa-api.yaml` | CPU/memory autoscaling |
| PDB | `pdb-api.yaml` | Zero-downtime drains |
| NetworkPolicy | `networkpolicy-api.yaml` | Least privilege |
| PVC | `pvc-knowledge.yaml` | Knowledge file storage |
| ServiceMonitor | `servicemonitor-api.yaml` | Prometheus Operator |

## Raw manifests

If you prefer plain YAML without Helm, render the chart:

```bash
helm template voxera deploy/helm/voxera \
  -f deploy/helm/voxera/values-production.yaml \
  > deploy/kubernetes/rendered.yaml
```

Review and apply with kubectl, or adopt GitOps (Argo CD / Flux).

## Blue/Green

1. Deploy green release: `helm upgrade --install voxera-green deploy/helm/voxera ...`
2. Validate health on green service
3. Switch Ingress backend or service selector
4. Retire blue release after soak period

See [kubernetes-guide.md](../../docs/operations/kubernetes-guide.md).
