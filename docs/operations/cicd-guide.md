# CI/CD Guide

## Pipelines

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push/PR to main, develop | Lint, test, security scan, build images, SBOM |
| `deploy-staging.yml` | Push to develop | Build + push images, Helm staging deploy |
| `deploy-production.yml` | Manual dispatch | Production deploy with approval gate |

## CI Stages

1. **Lint Python** — ruff, black
2. **Test Python** — pytest with Postgres service, Alembic migrations
3. **Dashboard** — build + vitest
4. **Web** — build
5. **Security** — pip-audit, Trivy filesystem scan
6. **Build Images** — API + dashboard (BuildKit cache)
7. **Infra Validation** — deployment asset tests
8. **SBOM** — SPDX JSON artifact

## GitHub Environments

Configure in repository settings:

| Environment | Protection |
|-------------|------------|
| `staging` | Auto-deploy from develop |
| `production` | Required reviewers, deployment branch main |

## Secrets (GitHub Actions)

| Secret | Purpose |
|--------|---------|
| `GITHUB_TOKEN` | GHCR push (default) |
| `KUBECONFIG_STAGING` | Staging cluster access |
| `KUBECONFIG_PRODUCTION` | Production cluster access |

## Image Registry

Images push to `ghcr.io/<org>/voxera-api`, `voxera-dashboard`, `voxera-web`.

Tag strategy:
- `staging` — latest develop build
- `<git-sha>` — immutable reference
- semver — release tags

## Production Deploy

```bash
# GitHub Actions → Deploy Production → input image_tag
# Or manually:
helm upgrade --install voxera deploy/helm/voxera \
  -f deploy/helm/voxera/values-production.yaml \
  --set api.image.tag=<sha> \
  --namespace voxera-prod
```

## Rollback

```bash
helm rollback voxera <revision> --namespace voxera-prod
```

Or redeploy previous image tag via workflow dispatch.

## Image Signing (Future)

Integrate cosign after push:

```bash
cosign sign ghcr.io/org/voxera-api@sha256:...
```
