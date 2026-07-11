"""Permission validation tests."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.core.enums import ToolPermissionEffect
from app.core.exceptions import CrossTenantToolError
from app.tools.schemas.execution import ToolPermissionRead
from app.tools.validators.access_validator import ToolAccessValidator, ToolPermissionEvaluator


def test_permission_blocks_tool():
    evaluator = ToolPermissionEvaluator()
    perms = [
        ToolPermissionRead(
            id=uuid4(),
            tenant_id=uuid4(),
            agent_id=None,
            tool_slug="refund",
            effect=ToolPermissionEffect.BLOCK,
            department=None,
            role=None,
            max_executions_per_hour=None,
            working_hours_start=None,
            working_hours_end=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    ]
    allowed, violations = evaluator.evaluate(tool_slug="refund", permissions=perms)
    assert allowed is False
    assert violations


def test_permission_allows_by_default():
    evaluator = ToolPermissionEvaluator()
    allowed, violations = evaluator.evaluate(tool_slug="appointment", permissions=[])
    assert allowed is True
    assert not violations


def test_cross_tenant_access_rejected():
    validator = ToolAccessValidator()
    with pytest.raises(CrossTenantToolError):
        validator.validate_scope(
            tenant_id=uuid4(),
            agent_id=uuid4(),
            resource_tenant_id=uuid4(),
        )
