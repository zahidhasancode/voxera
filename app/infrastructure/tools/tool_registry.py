"""ToolRegistry implementation — central orchestrator for tool execution."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.enums import ToolAuditStatus, ToolFrameworkExecutionStatus
from app.core.exceptions import (
    ToolCircuitOpenError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolRateLimitError,
)
from app.tools.audit.audit_service import ToolAuditService
from app.tools.execution.executor import ToolExecutor
from app.tools.execution.timeout import timeout_status
from app.tools.interfaces.tool import Tool
from app.tools.metrics.collector import ToolMetricsCollector
from app.tools.registry.tool_registry import ToolRegistry
from app.tools.repository.execution import (
    TenantToolConfigRepository,
    ToolFrameworkExecutionRepository,
    ToolPermissionRepository,
)
from app.tools.schemas.execution import (
    TenantToolConfigRead,
    ToolDefinitionRead,
    ToolExecuteRequest,
    ToolExecutionContext,
    ToolExecutionRead,
    ToolExecutionResult,
    ToolMetricsSnapshot,
    ToolTestRequest,
)
from app.tools.validators.access_validator import ToolAccessValidator, ToolPermissionEvaluator
from app.tools.validators.guardrails_validator import ToolGuardrailsValidator
from app.tools.validators.input_validator import ToolInputValidator


class ToolRegistryImpl(ToolRegistry):
    """Production tool registry — Planner interacts ONLY with this class."""

    def __init__(
        self,
        *,
        plugins: dict[str, Tool],
        configs: TenantToolConfigRepository,
        permissions: ToolPermissionRepository,
        executions: ToolFrameworkExecutionRepository,
        audit: ToolAuditService,
        executor: ToolExecutor | None = None,
        metrics: ToolMetricsCollector | None = None,
    ) -> None:
        self._plugins = plugins
        self._configs = configs
        self._permissions = permissions
        self._executions = executions
        self._audit = audit
        self._executor = executor or ToolExecutor()
        self._metrics = metrics or ToolMetricsCollector()
        self._access = ToolAccessValidator()
        self._permission_eval = ToolPermissionEvaluator()
        self._input_validator = ToolInputValidator()
        self._guardrails = ToolGuardrailsValidator()

    async def list_tools(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        enabled_only: bool = True,
    ) -> list[ToolDefinitionRead]:
        configs = {c.tool_slug: c for c in await self._configs.list_for_tenant(tenant_id)}
        definitions: list[ToolDefinitionRead] = []
        for slug, tool in self._plugins.items():
            config = configs.get(slug)
            enabled = config.enabled if config else True
            if enabled_only and not enabled:
                continue
            definitions.append(self._to_definition(tool, enabled))
        return sorted(definitions, key=lambda d: d.slug)

    async def get_tool(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        tool_slug: str,
    ) -> ToolDefinitionRead:
        tool = self._resolve_plugin(tool_slug)
        config = await self._configs.get(tenant_id, tool_slug)
        enabled = config.enabled if config else True
        return self._to_definition(tool, enabled)

    async def enable_tool(self, tenant_id: UUID, tool_slug: str) -> None:
        self._resolve_plugin(tool_slug)
        await self._upsert_config(tenant_id, tool_slug, enabled=True)

    async def disable_tool(self, tenant_id: UUID, tool_slug: str) -> None:
        self._resolve_plugin(tool_slug)
        await self._upsert_config(tenant_id, tool_slug, enabled=False)

    async def execute(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: ToolExecuteRequest,
    ) -> ToolExecutionResult:
        return await self._run(
            tenant_id,
            agent_id,
            request,
            persist=not request.dry_run,
            test_mode=False,
        )

    async def test(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: ToolTestRequest,
    ) -> ToolExecutionResult:
        exec_request = ToolExecuteRequest(
            tool_slug=request.tool_slug,
            arguments=request.arguments,
            dry_run=True,
        )
        return await self._run(tenant_id, agent_id, exec_request, persist=False, test_mode=True)

    async def get_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
        tool_slug: str | None = None,
        limit: int = 50,
    ) -> list[ToolExecutionRead]:
        return await self._executions.list_history(
            tenant_id,
            agent_id,
            conversation_id=conversation_id,
            tool_slug=tool_slug,
            limit=limit,
        )

    async def get_metrics(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        tool_slug: str | None = None,
    ) -> ToolMetricsSnapshot:
        db_metrics = await self._executions.metrics_snapshot(tenant_id, agent_id, tool_slug=tool_slug)
        return self._metrics.merge_db_metrics(db_metrics)

    async def _run(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: ToolExecuteRequest,
        *,
        persist: bool,
        test_mode: bool,
    ) -> ToolExecutionResult:
        now = datetime.now(timezone.utc)
        tool = self._resolve_plugin(request.tool_slug)

        if not test_mode:
            await self._audit.log_request(
                tenant_id=tenant_id,
                agent_id=agent_id,
                conversation_id=request.conversation_id,
                tool_slug=request.tool_slug,
                planner_request=request.model_dump(mode="json"),
                operator=request.operator,
            )

        if request.idempotency_key and persist:
            existing = await self._executions.get_by_idempotency(
                tenant_id, agent_id, request.idempotency_key
            )
            if existing:
                self._metrics.record_cache_hit()
                return self._execution_to_result(existing, tenant_id, agent_id, now)

        self._metrics.record_cache_miss()

        config = await self._configs.get(tenant_id, request.tool_slug)
        if config and not config.enabled:
            return await self._fail_result(
                tenant_id=tenant_id,
                agent_id=agent_id,
                request=request,
                tool=tool,
                status=ToolFrameworkExecutionStatus.PERMISSION_DENIED,
                error="Tool disabled for tenant",
                now=now,
                persist=persist,
                permission_denied=True,
            )

        perm_violations = await self._check_permissions(
            tenant_id, agent_id, request.tool_slug, request.department, request.role
        )
        if perm_violations:
            return await self._fail_result(
                tenant_id=tenant_id,
                agent_id=agent_id,
                request=request,
                tool=tool,
                status=ToolFrameworkExecutionStatus.PERMISSION_DENIED,
                error="; ".join(perm_violations),
                now=now,
                persist=persist,
                permission_denied=True,
                metadata={"violations": perm_violations},
            )

        guard_violations = self._guardrails.validate_tool_slug(
            request.tool_slug, set(self._plugins.keys())
        )
        guard_violations.extend(self._guardrails.validate_arguments(request.arguments))
        if guard_violations:
            return await self._fail_result(
                tenant_id=tenant_id,
                agent_id=agent_id,
                request=request,
                tool=tool,
                status=ToolFrameworkExecutionStatus.VALIDATION_FAILED,
                error="; ".join(guard_violations),
                now=now,
                persist=persist,
                validation_failed=True,
                metadata={"violations": guard_violations},
            )

        schema_violations = self._input_validator.validate(tool.parameters(), request.arguments)
        schema_violations.extend(
            self._input_validator.validate_required_fields(tool.parameters(), request.arguments)
        )
        schema_violations.extend(await tool.validate(request.arguments))
        if schema_violations:
            return await self._fail_result(
                tenant_id=tenant_id,
                agent_id=agent_id,
                request=request,
                tool=tool,
                status=ToolFrameworkExecutionStatus.VALIDATION_FAILED,
                error="; ".join(schema_violations),
                now=now,
                persist=persist,
                validation_failed=True,
                metadata={"violations": schema_violations},
            )

        rate_limit = config.rate_limit_per_minute if config and config.rate_limit_per_minute else settings.TOOL_RATE_LIMIT_PER_MINUTE
        recent_count = await self._executions.count_since(tenant_id, agent_id, request.tool_slug, since_minutes=1)
        if recent_count >= rate_limit:
            raise ToolRateLimitError(f"Rate limit exceeded for {request.tool_slug}: {rate_limit}/min")

        if request.dry_run:
            return ToolExecutionResult(
                status=ToolFrameworkExecutionStatus.SUCCESS,
                tool_name=tool.name(),
                tool_slug=tool.slug(),
                execution_time_ms=0.0,
                result={"dry_run": True, "validated": True},
                metadata={"test_mode": test_mode},
                warnings=[],
                error=None,
                timestamp=now,
                conversation_id=request.conversation_id,
                tenant_id=tenant_id,
                agent_id=agent_id,
            )

        context = ToolExecutionContext(
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=request.conversation_id,
            tool_slug=request.tool_slug,
            arguments=request.arguments,
            provider_config=config.provider_config if config else None,
            credentials_ref=config.credentials_ref if config else None,
            timeout_seconds=config.timeout_seconds if config and config.timeout_seconds else settings.TOOL_EXECUTION_TIMEOUT_SECONDS,
            idempotency_key=request.idempotency_key,
        )

        try:
            payload, elapsed_ms, retry_count = await self._executor.run(tool, context)
            result = ToolExecutionResult(
                status=ToolFrameworkExecutionStatus.SUCCESS,
                tool_name=tool.name(),
                tool_slug=tool.slug(),
                execution_time_ms=elapsed_ms,
                result=payload,
                metadata={"retry_count": retry_count},
                warnings=[],
                error=None,
                timestamp=now,
                conversation_id=request.conversation_id,
                tenant_id=tenant_id,
                agent_id=agent_id,
            )
            execution_id = None
            if persist:
                saved = await self._persist_execution(
                    tenant_id, agent_id, request, tool, result, retry_count
                )
                execution_id = saved.id
                result.execution_id = execution_id
            self._metrics.record_execution(
                tool_slug=tool.slug(), success=True, latency_ms=elapsed_ms
            )
            await self._audit.log_outcome(
                tenant_id=tenant_id,
                agent_id=agent_id,
                conversation_id=request.conversation_id,
                tool_slug=request.tool_slug,
                execution_id=execution_id,
                status=ToolAuditStatus.COMPLETED,
                validated_arguments=request.arguments,
                result=result,
                duration_ms=elapsed_ms,
                operator=request.operator,
            )
            return result
        except ToolCircuitOpenError as exc:
            return await self._fail_result(
                tenant_id=tenant_id,
                agent_id=agent_id,
                request=request,
                tool=tool,
                status=ToolFrameworkExecutionStatus.CIRCUIT_OPEN,
                error=str(exc),
                now=now,
                persist=persist,
            )
        except Exception as exc:
            status = timeout_status(exc) if isinstance(exc, ToolExecutionError) else ToolFrameworkExecutionStatus.FAILED
            return await self._fail_result(
                tenant_id=tenant_id,
                agent_id=agent_id,
                request=request,
                tool=tool,
                status=status,
                error=str(exc),
                now=now,
                persist=persist,
            )

    async def _check_permissions(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        tool_slug: str,
        department: str | None,
        role: str | None,
    ) -> list[str]:
        perms = await self._permissions.list_for_tenant(tenant_id, agent_id=agent_id)
        executions_last_hour = await self._executions.count_since(
            tenant_id, agent_id, tool_slug, since_minutes=60
        )
        allowed, violations = self._permission_eval.evaluate(
            tool_slug=tool_slug,
            permissions=perms,
            department=department,
            role=role,
            executions_last_hour=executions_last_hour,
        )
        if not allowed:
            return violations
        return []

    async def _fail_result(
        self,
        *,
        tenant_id: UUID,
        agent_id: UUID,
        request: ToolExecuteRequest,
        tool: Tool,
        status: ToolFrameworkExecutionStatus,
        error: str,
        now: datetime,
        persist: bool,
        permission_denied: bool = False,
        validation_failed: bool = False,
        metadata: dict | None = None,
    ) -> ToolExecutionResult:
        result = ToolExecutionResult(
            status=status,
            tool_name=tool.name(),
            tool_slug=tool.slug(),
            execution_time_ms=0.0,
            result=None,
            metadata=metadata or {},
            warnings=[],
            error=error,
            timestamp=now,
            conversation_id=request.conversation_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
        )
        execution_id = None
        if persist:
            saved = await self._persist_execution(tenant_id, agent_id, request, tool, result, 0)
            execution_id = saved.id
            result.execution_id = execution_id
        self._metrics.record_execution(
            tool_slug=tool.slug(),
            success=False,
            latency_ms=0.0,
            permission_denied=permission_denied,
            validation_failed=validation_failed,
        )
        await self._audit.log_outcome(
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=request.conversation_id,
            tool_slug=request.tool_slug,
            execution_id=execution_id,
            status=ToolAuditStatus.FAILED if status != ToolFrameworkExecutionStatus.PERMISSION_DENIED else ToolAuditStatus.DENIED,
            validated_arguments=request.arguments,
            result=result,
            duration_ms=0.0,
            operator=request.operator,
            error=error,
        )
        return result

    async def _persist_execution(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: ToolExecuteRequest,
        tool: Tool,
        result: ToolExecutionResult,
        retry_count: int,
    ) -> ToolExecutionRead:
        now = datetime.now(timezone.utc)
        record = ToolExecutionRead(
            id=uuid4(),
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=request.conversation_id,
            tool_slug=tool.slug(),
            tool_name=tool.name(),
            status=result.status,
            arguments=request.arguments,
            result=result.result,
            error=result.error,
            execution_time_ms=result.execution_time_ms,
            retry_count=retry_count,
            idempotency_key=request.idempotency_key,
            created_at=now,
            updated_at=now,
        )
        return await self._executions.create(record)

    def _resolve_plugin(self, tool_slug: str) -> Tool:
        tool = self._plugins.get(tool_slug)
        if tool is None:
            raise ToolNotFoundError(f"Tool not registered: {tool_slug}")
        return tool

    async def _upsert_config(self, tenant_id: UUID, tool_slug: str, *, enabled: bool) -> None:
        existing = await self._configs.get(tenant_id, tool_slug)
        now = datetime.now(timezone.utc)
        config = TenantToolConfigRead(
            id=existing.id if existing else uuid4(),
            tenant_id=tenant_id,
            tool_slug=tool_slug,
            enabled=enabled,
            credentials_ref=existing.credentials_ref if existing else None,
            provider_config=existing.provider_config if existing else None,
            rate_limit_per_minute=existing.rate_limit_per_minute if existing else None,
            timeout_seconds=existing.timeout_seconds if existing else None,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        await self._configs.upsert(config)

    def _to_definition(self, tool: Tool, enabled: bool) -> ToolDefinitionRead:
        return ToolDefinitionRead(
            slug=tool.slug(),
            name=tool.name(),
            description=tool.description(),
            parameters=tool.parameters(),
            permission_scope=tool.permission_scope(),
            enabled=enabled,
        )

    def _execution_to_result(
        self,
        execution: ToolExecutionRead,
        tenant_id: UUID,
        agent_id: UUID,
        now: datetime,
    ) -> ToolExecutionResult:
        return ToolExecutionResult(
            status=execution.status,
            tool_name=execution.tool_name,
            tool_slug=execution.tool_slug,
            execution_time_ms=execution.execution_time_ms,
            result=execution.result,
            metadata={"idempotent_replay": True},
            warnings=["Returned cached idempotent execution"],
            error=execution.error,
            timestamp=now,
            conversation_id=execution.conversation_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            execution_id=execution.id,
        )
