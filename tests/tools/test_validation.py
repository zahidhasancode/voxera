"""Guardrails and input validation tests."""

import pytest

from app.tools.validators.guardrails_validator import ToolGuardrailsValidator
from app.tools.validators.input_validator import ToolInputValidator


def test_guardrails_block_sql_injection():
    validator = ToolGuardrailsValidator()
    violations = validator.validate_arguments({"query": "DROP TABLE users"})
    assert violations


def test_guardrails_block_unknown_tool():
    validator = ToolGuardrailsValidator()
    violations = validator.validate_tool_slug("evil_tool", {"appointment"})
    assert violations


def test_input_validator_required_fields():
    validator = ToolInputValidator()
    schema = {
        "type": "object",
        "properties": {"action": {"type": "string"}},
        "required": ["action"],
    }
    violations = validator.validate(schema, {})
    assert violations


@pytest.mark.asyncio
async def test_appointment_tool_validate():
    from app.tools.adapters.appointment import AppointmentTool

    tool = AppointmentTool()
    violations = await tool.validate({})
    assert violations
