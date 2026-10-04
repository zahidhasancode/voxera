"""Base class for built-in tool adapters."""

from abc import abstractmethod
from typing import Any

from app.tools.interfaces.tool import Tool


class BuiltinTool(Tool):
    """Shared validation and health for built-in tools."""

    @abstractmethod
    def slug(self) -> str:
        ...

    async def health(self) -> dict[str, Any]:
        return {"status": "healthy", "tool": self.slug()}

    async def validate(self, arguments: dict[str, Any]) -> list[str]:
        from app.tools.validators.input_validator import ToolInputValidator

        validator = ToolInputValidator()
        violations = validator.validate(self.parameters(), arguments)
        violations.extend(validator.validate_required_fields(self.parameters(), arguments))
        return violations

    def _require_fields(self, arguments: dict[str, Any], fields: list[str]) -> list[str]:
        return [f"missing_required: {f}" for f in fields if f not in arguments or arguments[f] in (None, "")]
