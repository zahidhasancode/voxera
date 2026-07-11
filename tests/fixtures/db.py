"""Database fixtures for integration tests."""

from __future__ import annotations

import os

import pytest

from app.database.session import close_database, init_database


def _database_configured() -> bool:
    return bool(os.environ.get("DATABASE_URL", "").strip())


@pytest.fixture(scope="session")
def database_configured() -> bool:
    return _database_configured()


@pytest.fixture
async def database_engine(database_configured):
    if not database_configured:
        pytest.skip("DATABASE_URL not configured")
    await init_database()
    yield
    await close_database()


@pytest.fixture
async def db_session(database_engine):
    from app.database.session import session_scope

    async with session_scope() as session:
        yield session
