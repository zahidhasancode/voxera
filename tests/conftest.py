"""Shared pytest configuration and auto-marking."""

from __future__ import annotations

import os

# Security keys for tests (must be set before app.core.config loads)
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-at-least-32-characters")
os.environ.setdefault("API_KEY_SECRET", "test-api-key-secret-at-least-32-characters")
os.environ.setdefault("ENCRYPTION_SECRET_KEY", "test-encryption-secret-32-chars!!")
os.environ.setdefault("SECRET_KEY", "test-legacy-secret-key-32-characters!!")
os.environ.setdefault("VOICE_REQUIRE_PROVIDERS", "false")
os.environ.setdefault("KNOWLEDGE_REQUIRE_PROVIDERS", "false")

import pytest  # noqa: E402

pytest_plugins = [
    "tests.fixtures.app",
    "tests.fixtures.http",
    "tests.fixtures.ids",
    "tests.fixtures.db",
]


def pytest_collection_modifyitems(config, items):
    """Auto-apply markers based on test path."""
    for item in items:
        path = str(item.fspath).replace("\\", "/")
        if "/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in path:
            item.add_marker(pytest.mark.e2e)
        elif "/security/" in path:
            item.add_marker(pytest.mark.security)
        elif "/chaos/" in path:
            item.add_marker(pytest.mark.chaos)
        elif "/load/" in path:
            item.add_marker(pytest.mark.slow)
        elif "/voice/" in path and "/e2e/" not in path and "/utilities/" not in path:
            if "test_e2e" not in path and "test_audio" not in path:
                pass
        elif "/infra/" in path:
            item.add_marker(pytest.mark.unit)
        elif not any(
            m.name in {"integration", "e2e", "security", "chaos", "slow", "benchmark"}
            for m in item.iter_markers()
        ):
            item.add_marker(pytest.mark.unit)
