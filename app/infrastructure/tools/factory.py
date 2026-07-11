"""Tool execution framework factory."""

from functools import lru_cache

from app.infrastructure.repositories.tool_framework.audit_repository import SqlAlchemyToolAuditRepository
from app.infrastructure.repositories.tool_framework.config_repository import SqlAlchemyTenantToolConfigRepository
from app.infrastructure.repositories.tool_framework.execution_repository import (
    SqlAlchemyToolFrameworkExecutionRepository,
)
from app.infrastructure.repositories.tool_framework.permission_repository import (
    SqlAlchemyToolPermissionRepository,
)
from app.infrastructure.tools.tool_registry import ToolRegistryImpl
from app.tools.audit.audit_service import ToolAuditService
from app.tools.execution.circuit_breaker import CircuitBreakerRegistry
from app.tools.execution.executor import ToolExecutor
from app.tools.execution.retry import RetryStrategy
from app.tools.metrics.collector import ToolMetricsCollector
from app.tools.registry.builtin_registry import build_builtin_tools
from app.tools.registry.tool_registry import ToolRegistry


@lru_cache
def get_tool_metrics_collector() -> ToolMetricsCollector:
    return ToolMetricsCollector()


@lru_cache
def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    return CircuitBreakerRegistry()


@lru_cache
def get_tool_plugins() -> dict:
    return build_builtin_tools()


def build_tool_registry(session) -> ToolRegistry:
    metrics = get_tool_metrics_collector()
    executor = ToolExecutor(
        retry=RetryStrategy(),
        circuit_registry=get_circuit_breaker_registry(),
    )
    audit_repo = SqlAlchemyToolAuditRepository(session)
    return ToolRegistryImpl(
        plugins=get_tool_plugins(),
        configs=SqlAlchemyTenantToolConfigRepository(session),
        permissions=SqlAlchemyToolPermissionRepository(session),
        executions=SqlAlchemyToolFrameworkExecutionRepository(session),
        audit=ToolAuditService(audit_repo),
        executor=executor,
        metrics=metrics,
    )
