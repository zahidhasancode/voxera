"""Health check tests."""

import pytest

from app.core.health import check_domain_modules, check_embedding_provider, live_check


@pytest.mark.asyncio
async def test_live_check_always_healthy():
    payload = await live_check()
    assert payload["status"] == "healthy"
    assert "version" in payload
    assert "pid" in payload


def test_domain_modules_loadable():
    modules = check_domain_modules()
    assert "planner" in modules
    assert "verifier" in modules
    assert modules["planner"]["status"] == "healthy"


def test_embedding_provider_skipped_when_unconfigured(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER", None)
    result = check_embedding_provider()
    assert result["status"] == "skipped"
