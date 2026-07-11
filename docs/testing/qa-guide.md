# QA Guide

## Running tests locally

### Prerequisites

```bash
pip install -r requirements-dev.txt
```

### Unit tests (default)

```bash
pytest tests/ -m unit -q
```

### Integration (Postgres required)

```bash
export DATABASE_URL=postgresql+asyncpg://voxera:voxera@localhost:5432/voxera_test
alembic upgrade head
pytest tests/integration/ -m integration -v
```

### Security

```bash
pytest tests/security/ -m security -v
```

### E2E (golden + voice)

```bash
pytest tests/e2e/ -m e2e -v
```

### Full QA suite

```bash
./scripts/run-qa-suite.sh full
```

## Dashboard tests

```bash
cd dashboard && npm run test
```

## Writing new tests

1. Place tests in the appropriate directory (`tests/<subsystem>/` for unit, `tests/integration/` etc. for cross-cutting).
2. Use fixtures from `tests/fixtures/` — do not duplicate app/client setup.
3. Mark slow or external tests explicitly.
4. Prefer deterministic assertions; avoid time-based sleeps except in voice sim (bounded).

## Fixture reference

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `app` | session | FastAPI application |
| `http_client` | function | Async HTTP client |
| `tenant_id` | function | Stable tenant UUID |
| `database_engine` | function | DB init when configured |

## CI alignment

PRs must pass the `pr` profile of `scripts/run-qa-suite.sh` equivalent jobs in GitHub Actions.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `DATABASE_URL not configured` | Expected for local unit runs; set URL for integration |
| Async fixture scope errors | Keep async fixtures function-scoped |
| Golden intent failures | Update dataset utterances to match classifier patterns; file regression if model changes |
