#!/usr/bin/env bash
set -euo pipefail

cd /app

if [[ "${RUN_MIGRATIONS:-true}" == "true" ]] && [[ -n "${DATABASE_URL:-}" ]]; then
  echo "[entrypoint] Running Alembic migrations..."
  alembic upgrade head
fi

if [[ "${VALIDATE_CONFIG:-true}" == "true" ]]; then
  echo "[entrypoint] Validating configuration..."
  python /app/scripts/validate-env.py
fi

WORKERS="${WORKERS:-1}"
if [[ "${WORKERS}" =~ ^[0-9]+$ ]] && [[ "${WORKERS}" -gt 1 ]] && [[ "${1:-}" == "uvicorn" ]]; then
  echo "[entrypoint] Starting uvicorn with ${WORKERS} workers"
  exec uvicorn app.main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
    --workers "${WORKERS}" \
    --proxy-headers \
    --forwarded-allow-ips "*"
fi

echo "[entrypoint] Executing: $*"
exec "$@"
