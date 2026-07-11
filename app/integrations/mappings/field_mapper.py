"""Field mapping engine — configurable, no hardcoded mappings."""

from __future__ import annotations

from typing import Any


class FieldMapper:
    """Apply tenant-defined field mappings to normalized records."""

    def apply_mappings(
        self,
        entity_type: str,
        records: list[dict[str, Any]],
        mappings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        active = [m for m in mappings if m.get("is_active", True) and m.get("entity_type") == entity_type]
        if not active:
            return records

        mapped: list[dict[str, Any]] = []
        for record in records:
            out: dict[str, Any] = {"_source": record}
            for mapping in active:
                source = mapping["source_field"]
                target = mapping["target_field"]
                value = self._extract(record, source)
                if value is not None:
                    out[target] = self._transform(value, mapping.get("transform"))
            mapped.append(out)
        return mapped

    def _extract(self, record: dict[str, Any], path: str) -> Any:
        parts = path.split(".")
        current: Any = record
        for part in parts:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    def _transform(self, value: Any, transform: dict[str, Any] | None) -> Any:
        if not transform:
            return value
        op = transform.get("op")
        if op == "lowercase" and isinstance(value, str):
            return value.lower()
        if op == "uppercase" and isinstance(value, str):
            return value.upper()
        if op == "prefix" and isinstance(value, str):
            return f"{transform.get('value', '')}{value}"
        return value


field_mapper = FieldMapper()
