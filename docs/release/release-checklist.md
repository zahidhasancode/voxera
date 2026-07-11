# VOXERA v1.0.0-RC1 — Release Checklist

## Pre-tag

- [ ] All CI jobs green on `main`
- [ ] `./scripts/run-qa-suite.sh full` passes
- [ ] `alembic upgrade head` tested on staging DB
- [ ] CHANGELOG.md updated
- [ ] Known issues reviewed and accepted by release board
- [ ] Security checklist completed ([security-checklist-rc1.md](security-checklist-rc1.md))
- [ ] Docker images built and scanned
- [ ] Helm chart linted

## Tag

```bash
git tag -a v1.0.0-RC1 -m "VOXERA Release Candidate 1"
git push origin v1.0.0-RC1
```

## Post-tag

- [ ] SBOM archived (`voxera-sbom.spdx.json`)
- [ ] Release notes published
- [ ] Design partner communication sent
- [ ] Staging deployment verified
- [ ] Rollback procedure documented and tested

## Rollback

1. `helm rollback voxera-api <revision>` or redeploy previous image tag
2. `alembic downgrade -1` only if migration is reversible (verify first)
3. Restore Postgres from backup if schema/data migration failed

See [go-live-checklist.md](go-live-checklist.md) for production deployment.
