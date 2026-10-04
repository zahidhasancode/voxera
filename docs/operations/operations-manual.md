# Operations Manual

## Daily Checks

- [ ] `/api/v1/health/ready` returns 200 on all regions
- [ ] Prometheus alerts clear (error rate, latency, voice queue)
- [ ] Grafana dashboards: API p95, voice latency, active calls
- [ ] Postgres connection pool utilization
- [ ] Knowledge ingestion queue (no stuck jobs)

## Key Dashboards

| Dashboard | Metrics |
|-----------|---------|
| API | `voxera_http_requests_total`, latency p95/p99, errors |
| Voice | `voxera_voice_first_audio_ms`, `voxera_audio_queue_wait_ms`, queue depth, dropped frames |
| Infrastructure | CPU, memory, pod restarts, HPA desired replicas |

Access Grafana: `http://<host>:3000` (compose monitoring stack)

## Configuration Changes

1. Update ConfigMap / `.env.production`
2. Rolling restart API pods
3. Verify readiness before closing change ticket

Never change secrets in ConfigMaps — use Kubernetes Secrets or external secret manager.

## Log Correlation

Structured JSON logs include correlation IDs via `RequestContextMiddleware`. Search logs by `request_id` across API instances.

## Maintenance Windows

1. Scale HPA min replicas up before maintenance
2. Drain nodes with respect to PDB
3. Run Alembic migrations before traffic switch (entrypoint `RUN_MIGRATIONS=true`)
4. Post-maintenance: deep health check + smoke test voice call

## Capacity Planning

Target per API pod (4 workers):
- ~200 concurrent WebSocket connections (tune via `WEBSOCKET_MAX_CONNECTIONS`)
- ~500 req/s REST (depends on endpoint mix)

Scale horizontally when:
- CPU sustained > 65%
- p95 latency > 500ms
- Voice queue depth > 100

## On-Call Escalation

See [Incident Response Guide](./incident-response.md).
