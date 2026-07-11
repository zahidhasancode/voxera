# Contributing to VOXERA

Thank you for contributing to VOXERA. This guide covers development workflow for enterprise contributors.

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 with pgvector (for integration tests)
- Docker (optional, for compose/infra validation)

## Setup

```bash
git clone <repo-url> && cd VOXERA
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Dashboard:

```bash
cd dashboard && npm install && npm run dev
```

## Development Commands

| Command | Purpose |
|---------|---------|
| `pytest tests/ -m unit -q` | Fast unit tests |
| `pytest tests/ -q` | Full Python suite |
| `./scripts/run-qa-suite.sh pr` | PR quality gate |
| `ruff check app/ tests/` | Lint |
| `black --check app/ tests/` | Format check |
| `cd dashboard && npm run test` | Dashboard tests |

## Branch Strategy

- `main` — release-ready, protected
- `develop` — integration branch
- `feature/*`, `fix/*`, `docs/*` — short-lived branches

## Pull Request Requirements

1. All CI checks pass
2. Tests for behavior changes
3. No secrets in commits
4. Documentation updated for user-facing changes
5. ADR for architectural decisions

## Code Standards

- Follow existing ports/adapters patterns (`app/<domain>/` + `app/infrastructure/`)
- No business logic in route handlers
- Tenant-scoped resources must include `tenant_id` validation
- Encrypted storage for secrets — never log credentials

## Reporting Issues

Use GitHub Issues with: environment, steps to reproduce, expected vs actual, logs (redacted).

See [docs/developer-guide.md](docs/developer-guide.md) for full reference.
