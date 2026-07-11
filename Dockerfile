# =============================================================================
# VOXERA API — production multi-stage image
# =============================================================================
# Build:  docker build -t voxera-api:latest .
# Run:    docker run -p 8000:8000 --env-file .env voxera-api:latest
# =============================================================================

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-prod.txt ./
RUN pip install --prefix=/install -r requirements-prod.txt

# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_HOME=/app \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 voxera \
    && useradd --uid 10001 --gid voxera --shell /usr/sbin/nologin --create-home voxera

COPY --from=builder /install /usr/local

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/docker-entrypoint.sh scripts/healthcheck.py scripts/validate-env.py ./scripts/
RUN chmod +x /app/scripts/docker-entrypoint.sh

RUN mkdir -p logs /data/knowledge \
    && chown -R voxera:voxera /app /data/knowledge

USER voxera

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD ["python", "/app/scripts/healthcheck.py", "--url", "http://127.0.0.1:8000/api/v1/health/ready"]

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
