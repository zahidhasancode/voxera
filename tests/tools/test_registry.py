"""Unit tests for ToolRegistry."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.enums import ToolBuiltinSlug, ToolFrameworkExecutionStatus
from app.core.exceptions import ToolNotFoundError
from app.infrastructure.tools.tool_registry import ToolRegistryImpl
from app.tools.adapters.appointment import AppointmentTool
from app.tools.audit.audit_service import ToolAuditService
from app.tools.execution.executor import ToolExecutor
from app.tools.metrics.collector import ToolMetricsCollector
from app.tools.schemas.execution import ToolExecuteRequest, ToolTestRequest


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def agent_id():
    return uuid4()


def _registry(plugins=None):
    configs = AsyncMock()
    configs.get = AsyncMock(return_value=None)
    configs.list_for_tenant = AsyncMock(return_value=[])
    permissions = AsyncMock()
    permissions.list_for_tenant = AsyncMock(return_value=[])
    executions = AsyncMock()
    executions.count_since = AsyncMock(return_value=0)
    executions.create = AsyncMock(side_effect=lambda r: r)
    executions.get_by_idempotency = AsyncMock(return_value=None)
    audit_repo = AsyncMock()
    audit_repo.append = AsyncMock(side_effect=lambda a: a)
    audit = ToolAuditService(audit_repo)
    return ToolRegistryImpl(
        plugins=plugins or {ToolBuiltinSlug.APPOINTMENT: AppointmentTool()},
        configs=configs,
        permissions=permissions,
        executions=executions,
        audit=audit,
        executor=ToolExecutor(),
        metrics=ToolMetricsCollector(),
    )


@pytest.mark.asyncio
async def test_list_tools_returns_builtin(tenant_id, agent_id):
    registry = _registry()
    tools = await registry.list_tools(tenant_id, agent_id)
    assert len(tools) == 1
    assert tools[0].slug == ToolBuiltinSlug.APPOINTMENT


@pytest.mark.asyncio
async def test_execute_appointment_book(tenant_id, agent_id):
    registry = _registry()
    result = await registry.execute(
        tenant_id,
        agent_id,
        ToolExecuteRequest(
            tool_slug=ToolBuiltinSlug.APPOINTMENT,
            arguments={"action": "book", "customer_name": "Jane"},
        ),
    )
    assert result.status == ToolFrameworkExecutionStatus.SUCCESS
    assert result.result["action"] == "book"
    assert "appointment_id" in result.result


@pytest.mark.asyncio
async def test_test_tool_dry_run(tenant_id, agent_id):
    registry = _registry()
    result = await registry.test(
        tenant_id,
        agent_id,
        ToolTestRequest(
            tool_slug=ToolBuiltinSlug.APPOINTMENT,
            arguments={"action": "book"},
        ),
    )
    assert result.result["dry_run"] is True


@pytest.mark.asyncio
async def test_unknown_tool_raises(tenant_id, agent_id):
    registry = _registry()
    with pytest.raises(ToolNotFoundError):
        await registry.get_tool(tenant_id, agent_id, "nonexistent")


@pytest.mark.asyncio
async def test_validation_failure_missing_required(tenant_id, agent_id):
    registry = _registry()
    result = await registry.execute(
        tenant_id,
        agent_id,
        ToolExecuteRequest(tool_slug=ToolBuiltinSlug.APPOINTMENT, arguments={}),
    )
    assert result.status == ToolFrameworkExecutionStatus.VALIDATION_FAILED


@pytest.mark.asyncio
async def test_idempotency_replay(tenant_id, agent_id):
    from app.tools.schemas.execution import ToolExecutionRead

    now = datetime.now(timezone.utc)
    existing = ToolExecutionRead(
        id=uuid4(),
        tenant_id=tenant_id,
        agent_id=agent_id,
        conversation_id=None,
        tool_slug=ToolBuiltinSlug.APPOINTMENT,
        tool_name="Book Appointment",
        status=ToolFrameworkExecutionStatus.SUCCESS,
        arguments={"action": "book"},
        result={"appointment_id": "abc"},
        error=None,
        execution_time_ms=10.0,
        retry_count=0,
        idempotency_key="key-1",
        created_at=now,
        updated_at=now,
    )
    registry = _registry()
    registry._executions.get_by_idempotency = AsyncMock(return_value=existing)
    result = await registry.execute(
        tenant_id,
        agent_id,
        ToolExecuteRequest(
            tool_slug=ToolBuiltinSlug.APPOINTMENT,
            arguments={"action": "book"},
            idempotency_key="key-1",
        ),
    )
    assert result.metadata.get("idempotent_replay") is True
