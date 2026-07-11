"""Workflow validator and plugin tests."""

import pytest

from app.core.enums import WorkflowExecutionStatus, WorkflowState
from app.workflow.engine.plugins import CompleteActionPlugin, WorkflowPluginRegistry
from app.workflow.validators.workflow_validator import WorkflowValidator
from app.workflow.schemas import ValidateWorkflowRequest


def test_validate_missing_slug_or_name():
    validator = WorkflowValidator()
    violations = validator.validate_definition(ValidateWorkflowRequest(definition={}))
    assert "missing_slug_or_name" in violations


def test_validate_valid_definition():
    validator = WorkflowValidator()
    violations = validator.validate_definition(
        ValidateWorkflowRequest(
            definition={
                "slug": "refund-flow",
                "name": "Refund Flow",
                "steps": [],
                "rules": [],
                "approval_chain": [],
            }
        )
    )
    assert violations == []


@pytest.mark.asyncio
async def test_complete_plugin():
    plugin = CompleteActionPlugin()
    result = await plugin.execute({}, {})
    assert result.state == WorkflowState.COMPLETED
    assert result.status == WorkflowExecutionStatus.COMPLETED
    assert result.completed


def test_plugin_registry_auto_registers():
    registry = WorkflowPluginRegistry()
    assert registry.get("notify") is not None
    assert registry.get("complete") is not None
