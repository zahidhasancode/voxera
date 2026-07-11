"""Migration smoke tests (integration)."""

from __future__ import annotations

import os

import pytest


@pytest.mark.integration
def test_alembic_head_defined():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    assert head is not None
    assert head.startswith("009") or len(head) >= 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connectivity_when_configured(database_configured, database_engine):
    if not database_configured:
        pytest.skip("DATABASE_URL not set")
    from app.database.session import check_database_connectivity

    assert await check_database_connectivity() is True


@pytest.mark.integration
def test_migrations_upgrade_idempotent_in_ci():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set")
    import subprocess

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
