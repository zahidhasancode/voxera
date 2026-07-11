#!/usr/bin/env bash
# PostgreSQL backup script for Docker Compose / cron
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backup}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
FILE="${BACKUP_DIR}/voxera-${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

POSTGRES_USER="${POSTGRES_USER:-voxera}"
POSTGRES_DB="${POSTGRES_DB:-voxera}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"

echo "Backing up ${POSTGRES_DB} to ${FILE}..."
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "${POSTGRES_USER}" -Fc "${POSTGRES_DB}" > "${FILE}"

echo "Backup complete: ${FILE} ($(du -h "${FILE}" | cut -f1))"
