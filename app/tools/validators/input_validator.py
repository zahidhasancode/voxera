"""Input validation against JSON Schema."""

from typing import Any

from jsonschema import Draft202012Validator


class ToolInputValidator:
    """Validates tool arguments against declared JSON Schema."""

    def validate(self, schema: dict[str, Any], arguments: dict[str, Any]) -> list[str]:
        if not schema:
            if arguments:
                return ["unexpected_arguments: tool accepts no parameters"]
            return []

        validator = Draft202012Validator(schema)
        violations: list[str] = []
        for error in sorted(validator.iter_errors(arguments), key=lambda e: e.path):
            path = ".".join(str(p) for p in error.path) or "root"
            violations.append(f"{path}: {error.message}")
        return violations

    def validate_required_fields(self, schema: dict[str, Any], arguments: dict[str, Any]) -> list[str]:
        required = schema.get("required", [])
        missing = [field for field in required if field not in arguments]
        if missing:
            return [f"missing_required: {', '.join(missing)}"]
        return []
