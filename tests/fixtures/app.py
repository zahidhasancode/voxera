"""FastAPI application fixtures."""

from __future__ import annotations

import pytest

from app.main import create_application


@pytest.fixture(scope="session")
def app():
    return create_application()
