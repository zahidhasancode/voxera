# Backup & Restore Guide

## PostgreSQL

### Backup (daily recommended)

```bash
# Docker Compose
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U voxera -Fc voxera > backup/voxera-$(date +%Y%m%d).dump

# Kubernetes (example CronJob)
kubectl exec -it postgres-0 -- pg_dump -U voxera -Fc voxera > backup.dump
```

### Restore

```bash
# Stop API to prevent writes
docker compose -f docker-compose.prod.yml stop api

docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_restore -U voxera -d voxera --clean --if-exists < backup/voxera-20260711.dump

docker compose -f docker-compose.prod.yml start api
```

### Point-in-Time Recovery

Use managed Postgres (RDS, Cloud SQL, Azure Database) with PITR enabled for production.

## Vector Data (pgvector)

Embeddings live in PostgreSQL — included in Postgres backup. Verify after restore:

```sql
SELECT COUNT(*) FROM knowledge_embeddings;
```

## Knowledge Files

PVC / volume at `KNOWLEDGE_STORAGE_PATH` (`/data/knowledge`):

```bash
# Backup
docker run --rm -v voxera-prod_knowledge_data:/data -v $(pwd)/backup:/backup \
  alpine tar czf /backup/knowledge-$(date +%Y%m%d).tar.gz -C /data .

# Restore
docker run --rm -v voxera-prod_knowledge_data:/data -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/knowledge-20260711.tar.gz -C /data
```

For S3-backed storage (future), enable versioning and cross-region replication.

## Configuration Backup

- Helm values: store in Git (no secrets)
- Secrets: export from secret manager, encrypted offline store
- `.env.production`: template only in repo (`deploy/env/.env.production.example`)

## Disaster Recovery RTO/RPO Targets

| Tier | RPO | RTO |
|------|-----|-----|
| Postgres | 1 hour | 4 hours |
| Knowledge files | 24 hours | 8 hours |
| Config/secrets | 0 (Git + secret manager) | 1 hour |

## DR Drill (Quarterly)

1. Restore Postgres to isolated environment
2. Restore knowledge volume
3. Deploy API with production-equivalent config
4. Run health checks + sample voice call
5. Document actual RTO achieved
