"""Integration provider registry tests."""

import pytest

from app.integrations.providers.registry import integration_provider_registry


@pytest.mark.unit
def test_registry_lists_all_providers():
    slugs = integration_provider_registry.list_slugs()
    assert len(slugs) >= 45
    assert "hubspot" in slugs
    assert "salesforce" in slugs
    assert "shopify" in slugs
    assert "zendesk" in slugs
    assert "stripe" in slugs


@pytest.mark.unit
def test_provider_metadata_structure():
    provider = integration_provider_registry.get("hubspot")
    meta = provider.metadata
    assert meta.slug.value == "hubspot"
    assert meta.category.value == "crm"
    assert len(meta.supported_entities) >= 1


@pytest.mark.unit
def test_unknown_provider_raises():
    with pytest.raises(KeyError):
        integration_provider_registry.get("nonexistent_provider")
