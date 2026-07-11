"""Tool registration and argument validation."""

from app.core.enums import PlannerAction
from app.tools.validators.input_validator import ToolInputValidator
from app.verifier.schemas import ValidationContext


class ToolValidator:
    def __init__(self) -> None:
        self._input = ToolInputValidator()

    def validate(self, ctx: ValidationContext) -> list[str]:
        violations: list[str] = []
        plan = ctx.verifier_input.planner_output
        registered = {t.slug for t in ctx.verifier_input.allowed_tools if t.enabled}
        ctx.registered_tool_slugs = registered

        if plan.action != PlannerAction.CALL_TOOL:
            return violations

        if not plan.tool_call:
            violations.append("tool_call_missing")
            return violations

        slug = plan.tool_call.tool_slug
        if slug not in registered:
            violations.append(f"unknown_tool:{slug}")
            return violations

        tool_def = next(t for t in ctx.verifier_input.allowed_tools if t.slug == slug)
        schema_violations = self._input.validate(tool_def.parameters or {}, plan.tool_call.arguments)
        schema_violations.extend(
            self._input.validate_required_fields(tool_def.parameters or {}, plan.tool_call.arguments)
        )
        violations.extend(schema_violations)

        dangerous_patterns = ("DROP TABLE", "rm -rf", "eval(", "exec(", "__import__")
        args_str = str(plan.tool_call.arguments)
        for pattern in dangerous_patterns:
            if pattern.lower() in args_str.lower():
                violations.append(f"dangerous_argument_pattern:{pattern}")

        return violations
