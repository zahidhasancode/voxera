"""OAuth manager tests."""

import pytest

from app.integrations.oauth.manager import IntegrationOAuthManager


@pytest.mark.unit
def test_compute_expiry_from_expires_in():
    manager = IntegrationOAuthManager()
    expiry = manager.compute_expiry({"expires_in": 3600})
    assert expiry is not None


@pytest.mark.unit
def test_compute_expiry_missing():
    manager = IntegrationOAuthManager()
    assert manager.compute_expiry({}) is None
