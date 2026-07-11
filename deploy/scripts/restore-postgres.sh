#!/usr/bin/env bash
# Restore PostgreSQL from pg_dump custom format
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup.dump>"
  exit 1
fi

BACKUP_FILE="$1"
POSTGRES_USER="${POSTGRES_USER:-voxera}"
POSTGRES_DB="${POSTGRES_DB:-voxera}"

echo "Stopping API to prevent writes..."
docker compose -f docker-compose.prod.yml stop api worker 2>/dev/null || true

echo "Restoring ${BACKUP_FILE}..."
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --clean --if-exists < "${BACKUP_FILE}"

echo "Starting API..."
docker compose -f docker-compose.prod.yml start api worker 2>/dev/null || \
  docker compose -f docker-compose.prod.yml start api

echo "Restore complete. Verify: curl /api/v1/health/ready"
