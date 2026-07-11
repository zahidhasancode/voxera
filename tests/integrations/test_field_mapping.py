"""Field mapping engine tests."""

import pytest

from app.integrations.mappings.field_mapper import field_mapper


@pytest.mark.unit
def test_apply_mappings_nested_source():
    records = [{"properties": {"email": "a@example.com"}}]
    mappings = [
        {
            "entity_type": "customer",
            "source_field": "properties.email",
            "target_field": "email",
            "is_active": True,
        }
    ]
    result = field_mapper.apply_mappings("customer", records, mappings)
    assert result[0]["email"] == "a@example.com"


@pytest.mark.unit
def test_no_mappings_passthrough():
    records = [{"id": "1"}]
    assert field_mapper.apply_mappings("customer", records, []) == records


@pytest.mark.unit
def test_transform_lowercase():
    records = [{"name": "ACME"}]
    mappings = [
        {
            "entity_type": "customer",
            "source_field": "name",
            "target_field": "name",
            "transform": {"op": "lowercase"},
            "is_active": True,
        }
    ]
    result = field_mapper.apply_mappings("customer", records, mappings)
    assert result[0]["name"] == "acme"
