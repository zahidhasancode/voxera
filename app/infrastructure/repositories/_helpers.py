"""Shared SQLAlchemy repository helpers."""

from typing import Any

from pydantic import BaseModel


def apply_partial_update(model: object, data: BaseModel, *, exclude_unset: bool = True) -> None:
    """Apply Pydantic update schema fields onto an ORM instance."""
    payload = data.model_dump(exclude_unset=exclude_unset)
    for key, value in payload.items():
        if key == "metadata":
            setattr(model, "metadata_", value)
        else:
            setattr(model, key, value)


def enum_values(data: BaseModel) -> dict[str, Any]:
    """Dump schema with enum values as strings for ORM assignment."""
    return data.model_dump(mode="json")
