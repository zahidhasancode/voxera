"""WorkflowEngine implementation."""

import time
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.enums import (
    EscalationTarget,
    RuleActionType,
    WorkflowEventType,
    WorkflowExecutionStatus,
    WorkflowState,
)
from app.core.exceptions import WorkflowNotFoundError, WorkflowPolicyViolationError
from app.workflow.approvals.approval_engine import ApprovalEngine
from app.workflow.audit.audit_service import WorkflowAuditService
from app.workflow.engine.event_bus import WorkflowEventBus
from app.workflow.engine.plugins import WorkflowPluginRegistry
from app.workflow.engine.workflow_engine import WorkflowEngine
from app.workflow.escalation.escalation_engine import EscalationEngine
from app.workflow.metrics.collector import WorkflowMetricsCollector
from app.workflow.policy.policy_engine import PolicyEngine
from app.workflow.routing.routing_engine import RoutingEngine
from app.workflow.rules.rule_engine import RuleEngine
from app.workflow.scheduler.scheduler import WorkflowScheduler
from app.workflow.schemas import (
    AdvanceWorkflowRequest,
    ApproveWorkflowRequest,
    RoutingRuleDefinition,
    StartWorkflowRequest,
    TestWorkflowRequest,
    ValidateWorkflowRequest,
    WorkflowEvent,
    WorkflowExecutionRead,
    WorkflowMetricsSnapshot,
    WorkflowRead,
    WorkflowRuleDefinition,
    WorkflowStepResult,
)
from app.workflow.validators.access_validator import WorkflowAccessValidator
from app.workflow.validators.workflow_validator import WorkflowValidator


class WorkflowEngineImpl(WorkflowEngine):
    def __init__(
        self,
        *,
        workflows,
        executions,
        rules_repo,
        policies_repo,
        routing_repo,
        audit: WorkflowAuditService,
        rule_engine: RuleEngine | None = None,
        policy_engine: PolicyEngine | None = None,
        approval_engine: ApprovalEngine | None = None,
        escalation_engine: EscalationEngine | None = None,
        routing_engine: RoutingEngine | None = None,
        scheduler: WorkflowScheduler | None = None,
        event_bus: WorkflowEventBus | None = None,
        plugins: WorkflowPluginRegistry | None = None,
        validator: WorkflowValidator | None = None,
        access: WorkflowAccessValidator | None = None,
        metrics: WorkflowMetricsCollector | None = None,
    ) -> None:
        self._workflows = workflows
        self._executions = executions
        self._rules_repo = rules_repo
        self._policies_repo = policies_repo
        self._routing_repo = routing_repo
        self._audit = audit
        self._rules = rule_engine or RuleEngine()
        self._policy = policy_engine or PolicyEngine()
        self._approval = approval_engine or ApprovalEngine()
        self._escalation = escalation_engine or EscalationEngine()
        self._routing = routing_engine or RoutingEngine()
        self._scheduler = scheduler or WorkflowScheduler()
        self._events = event_bus or WorkflowEventBus()
        self._plugins = plugins or WorkflowPluginRegistry()
        self._validator = validator or WorkflowValidator()
        self._access = access or WorkflowAccessValidator()
        self._metrics = metrics or WorkflowMetricsCollector()

    async def start(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: StartWorkflowRequest,
    ) -> WorkflowStepResult:
        start_time = time.perf_counter()
        workflow = await self._resolve_workflow(tenant_id, request)
        definition = workflow.definition

        context = {
            **request.context,
            "conversation_id": str(request.conversation_id),
            "planner_output": request.planner_output,
            "verifier_result": request.verifier_result,
        }

        policies = self._policy.merge_policies(await self._policies_repo.list_for_tenant(tenant_id))
        policy_violations = self._policy.evaluate(policies, context)
        if policy_violations and "outside_working_hours" in policy_violations[0]:
            can_exec, reason = self._scheduler.can_execute_now(policies, allow_delayed=False)
            if not can_exec:
                return WorkflowStepResult(
                    state=WorkflowState.WAITING_CUSTOMER,
                    status=WorkflowExecutionStatus.PAUSED,
                    policy_violations=policy_violations,
                    message=reason,
                )

        rule_defs = await self._load_rules(tenant_id, workflow.id, definition)
        actions = self._rules.evaluate(rule_defs, context)
        result = await self._apply_actions(actions, context, definition, policies, tenant_id, agent_id, request.conversation_id)

        now = datetime.now(timezone.utc)
        execution_id = uuid4()
        exec_read = WorkflowExecutionRead(
            id=execution_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            workflow_id=workflow.id,
            conversation_id=request.conversation_id,
            status=result.status,
            current_state=result.state,
            context={**context, "pending_approvals": context.get("pending_approvals", [])},
            step_index=1,
            retry_count=0,
            started_at=now,
            completed_at=now if result.completed else None,
            expires_at=now + timedelta(seconds=settings.WORKFLOW_DEFAULT_TIMEOUT_SECONDS),
            error=None,
            created_at=now,
            updated_at=now,
        )
        await self._executions.create(exec_read)

        await self._emit_event(
            tenant_id, agent_id, request.conversation_id, execution_id, WorkflowEventType.WORKFLOW_STARTED, context
        )

        elapsed = (time.perf_counter() - start_time) * 1000
        self._metrics.record_execution(
            completed=result.completed,
            failed=result.status == WorkflowExecutionStatus.FAILED,
            escalated=result.state == WorkflowState.ESCALATED,
            duration_ms=elapsed,
            steps=1,
            policy_violations=len(policy_violations),
        )
        result.policy_violations = policy_violations
        return result

    async def advance(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: AdvanceWorkflowRequest,
    ) -> WorkflowStepResult:
        execution = await self._require_execution(tenant_id, agent_id, request.execution_id)
        self._access.validate_scope(
            tenant_id=tenant_id, agent_id=agent_id,
            resource_tenant_id=execution.tenant_id, resource_agent_id=execution.agent_id,
        )

        context = {**(execution.context or {}), **request.context_updates}
        workflow = await self._workflows.get_by_id(tenant_id, execution.workflow_id)
        if not workflow:
            raise WorkflowNotFoundError("Workflow not found")

        policies = self._policy.merge_policies(await self._policies_repo.list_for_tenant(tenant_id))
        rule_defs = await self._load_rules(tenant_id, workflow.id, workflow.definition)
        actions = self._rules.evaluate(rule_defs, context)
        result = await self._apply_actions(
            actions, context, workflow.definition, policies, tenant_id, agent_id, execution.conversation_id
        )

        execution.status = result.status
        execution.current_state = result.state
        execution.context = context
        execution.step_index += 1
        if result.completed:
            execution.completed_at = datetime.now(timezone.utc)
        await self._executions.update(execution)

        if result.completed:
            await self._emit_event(
                tenant_id, agent_id, execution.conversation_id, execution.id,
                WorkflowEventType.WORKFLOW_COMPLETED, context,
            )
        return result

    async def approve(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: ApproveWorkflowRequest,
    ) -> WorkflowStepResult:
        execution = await self._require_execution(tenant_id, agent_id, request.execution_id)
        context = execution.context or {}
        pending = context.get("pending_approvals", [])
        result, updated = self._approval.process_decision(
            approvals=pending, approval_id=request.approval_id, approved=request.approved,
        )
        context["pending_approvals"] = updated
        execution.context = context
        execution.current_state = result.state
        execution.status = result.status
        if result.completed and not request.approved:
            execution.completed_at = datetime.now(timezone.utc)
        await self._executions.update(execution)

        event = WorkflowEventType.WORKFLOW_APPROVED if request.approved else WorkflowEventType.WORKFLOW_REJECTED
        await self._emit_event(tenant_id, agent_id, execution.conversation_id, execution.id, event, context, request.approver_id)
        return result

    async def pause(self, tenant_id: UUID, agent_id: UUID, execution_id: UUID) -> WorkflowStepResult:
        execution = await self._require_execution(tenant_id, agent_id, execution_id)
        execution.status = WorkflowExecutionStatus.PAUSED
        execution.current_state = WorkflowState.PAUSED
        await self._executions.update(execution)
        await self._emit_event(
            tenant_id, agent_id, execution.conversation_id, execution.id,
            WorkflowEventType.WORKFLOW_PAUSED, execution.context or {},
        )
        return WorkflowStepResult(state=WorkflowState.PAUSED, status=WorkflowExecutionStatus.PAUSED, actions_taken=["paused"])

    async def resume(self, tenant_id: UUID, agent_id: UUID, execution_id: UUID) -> WorkflowStepResult:
        execution = await self._require_execution(tenant_id, agent_id, execution_id)
        execution.status = WorkflowExecutionStatus.RUNNING
        execution.current_state = WorkflowState.EXECUTING
        await self._executions.update(execution)
        await self._emit_event(
            tenant_id, agent_id, execution.conversation_id, execution.id,
            WorkflowEventType.WORKFLOW_RESUMED, execution.context or {},
        )
        return WorkflowStepResult(state=WorkflowState.EXECUTING, status=WorkflowExecutionStatus.RUNNING, actions_taken=["resumed"])

    async def reject(self, tenant_id: UUID, agent_id: UUID, execution_id: UUID, *, reason: str) -> WorkflowStepResult:
        execution = await self._require_execution(tenant_id, agent_id, execution_id)
        execution.status = WorkflowExecutionStatus.REJECTED
        execution.current_state = WorkflowState.REJECTED
        execution.error = reason
        execution.completed_at = datetime.now(timezone.utc)
        await self._executions.update(execution)
        await self._emit_event(
            tenant_id, agent_id, execution.conversation_id, execution.id,
            WorkflowEventType.WORKFLOW_REJECTED, {"reason": reason},
        )
        return WorkflowStepResult(
            state=WorkflowState.REJECTED, status=WorkflowExecutionStatus.REJECTED,
            actions_taken=["rejected"], completed=True, message=reason,
        )

    async def test(self, tenant_id: UUID, agent_id: UUID, request: TestWorkflowRequest) -> WorkflowStepResult:
        context = request.context
        definition = request.definition or {}
        if request.workflow_slug:
            wf = await self._workflows.get_by_slug(tenant_id, request.workflow_slug)
            if wf:
                definition = wf.definition

        policies = self._policy.merge_policies(await self._policies_repo.list_for_tenant(tenant_id))
        rule_defs = [WorkflowRuleDefinition.model_validate(r) for r in definition.get("rules", [])]
        actions = self._rules.evaluate(rule_defs, context)
        return await self._apply_actions(
            actions, context, definition, policies, tenant_id, agent_id,
            UUID(str(context.get("conversation_id", uuid4()))),
        )

    async def validate(self, request: ValidateWorkflowRequest) -> list[str]:
        return self._validator.validate_definition(request)

    async def list_workflows(self, tenant_id: UUID) -> list[WorkflowRead]:
        return await self._workflows.list_for_tenant(tenant_id)

    async def get_workflow(self, tenant_id: UUID, workflow_id: UUID) -> WorkflowRead:
        wf = await self._workflows.get_by_id(tenant_id, workflow_id)
        if not wf:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")
        return wf

    async def get_execution(self, tenant_id: UUID, agent_id: UUID, execution_id: UUID) -> WorkflowExecutionRead:
        return await self._require_execution(tenant_id, agent_id, execution_id)

    async def get_history(self, tenant_id: UUID, agent_id: UUID, conversation_id: UUID, *, limit: int = 50) -> list:
        return await self._audit.list_history(tenant_id, agent_id, conversation_id, limit=limit)

    async def get_metrics(
        self, tenant_id: UUID, agent_id: UUID, *, conversation_id: UUID | None = None
    ) -> WorkflowMetricsSnapshot:
        db = await self._executions.metrics_snapshot(tenant_id, agent_id, conversation_id=conversation_id)
        snap = self._metrics.snapshot()
        if not db:
            return snap
        total = db.get("total_executions", 0) + snap.total_executions
        return WorkflowMetricsSnapshot(
            total_executions=total,
            completed_count=db.get("completed_count", 0) + snap.completed_count,
            failed_count=db.get("failed_count", 0) + snap.failed_count,
            escalated_count=db.get("escalated_count", 0) + snap.escalated_count,
            average_duration_ms=snap.average_duration_ms,
            average_approval_time_ms=snap.average_approval_time_ms,
            escalation_rate=(db.get("escalated_count", 0) + snap.escalated_count) / max(total, 1),
            success_rate=(db.get("completed_count", 0) + snap.completed_count) / max(total, 1),
            policy_violation_count=snap.policy_violation_count,
            average_steps=snap.average_steps,
            average_wait_time_ms=snap.average_wait_time_ms,
        )

    async def _apply_actions(
        self,
        actions,
        context: dict,
        definition: dict,
        policies,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> WorkflowStepResult:
        taken: list[str] = []
        result = WorkflowStepResult(
            state=WorkflowState.EXECUTING,
            status=WorkflowExecutionStatus.RUNNING,
        )

        is_vip = self._policy.is_vip(policies, context)
        planner = context.get("planner_output") or {}
        is_emergency = context.get("intent") == "emergency" or planner.get("intent") == "emergency"

        routing_rules = [
            RoutingRuleDefinition.model_validate(r)
            for r in definition.get("routing_rules", [])
        ] + [
            RoutingRuleDefinition.model_validate(r)
            for r in await self._routing_repo.list_for_tenant(tenant_id)
        ]
        route = self._routing.route(routing_rules, context, is_vip=is_vip, is_emergency=is_emergency)
        if route:
            result.routing_target = route
            taken.append(f"route:{route.get('strategy')}")

        for action in actions:
            if action.type == RuleActionType.REJECT:
                return WorkflowStepResult(
                    state=WorkflowState.REJECTED,
                    status=WorkflowExecutionStatus.REJECTED,
                    actions_taken=taken + ["rejected"],
                    completed=True,
                    message=action.params.get("reason", "Rejected by rule"),
                )
            if action.type == RuleActionType.REQUIRE_APPROVAL:
                step_result, pending = self._approval.evaluate(
                    approval_chain=definition.get("approval_chain", [{"role": action.params.get("role", "manager")}]),
                    context=context,
                )
                context["pending_approvals"] = pending
                step_result.routing_target = route
                step_result.actions_taken = taken + step_result.actions_taken
                return step_result
            if action.type == RuleActionType.ESCALATE:
                esc_result, _ = self._escalation.escalate(
                    target=action.params.get("target", EscalationTarget.HUMAN_AGENT),
                    reason=action.params.get("reason", "Rule escalation"),
                    context_snapshot=context,
                    escalation_policy=definition.get("escalation_policy"),
                )
                esc_result.routing_target = route
                esc_result.actions_taken = taken + esc_result.actions_taken
                return esc_result
            if action.type == RuleActionType.BYPASS_AUTH:
                context["bypass_auth"] = True
                taken.append("bypass_auth")
            if action.type == RuleActionType.COMPLETE:
                plugin_result = await self._plugins.execute_action("complete", action.params, context)
                if plugin_result:
                    plugin_result.routing_target = route
                    plugin_result.actions_taken = taken + plugin_result.actions_taken
                    return plugin_result

        result.actions_taken = taken or ["continue"]
        result.routing_target = route
        return result

    async def _load_rules(self, tenant_id: UUID, workflow_id: UUID, definition: dict) -> list:
        db_rules = await self._rules_repo.list_for_tenant(tenant_id, workflow_id=workflow_id)
        def_rules = definition.get("rules", [])
        all_rules = def_rules + db_rules
        return [WorkflowRuleDefinition.model_validate(r) for r in all_rules]

    async def _resolve_workflow(self, tenant_id: UUID, request: StartWorkflowRequest) -> WorkflowRead:
        if request.workflow_id:
            wf = await self._workflows.get_by_id(tenant_id, request.workflow_id)
        elif request.workflow_slug:
            wf = await self._workflows.get_by_slug(tenant_id, request.workflow_slug)
        else:
            wf = await self._workflows.get_by_slug(tenant_id, "default")
        if not wf:
            raise WorkflowNotFoundError("Workflow not found")
        return wf

    async def _require_execution(self, tenant_id: UUID, agent_id: UUID, execution_id: UUID) -> WorkflowExecutionRead:
        execution = await self._executions.get_by_id(tenant_id, execution_id)
        if not execution:
            raise WorkflowNotFoundError(f"Execution {execution_id} not found")
        self._access.validate_scope(
            tenant_id=tenant_id, agent_id=agent_id,
            resource_tenant_id=execution.tenant_id, resource_agent_id=execution.agent_id,
        )
        return execution

    async def _emit_event(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        execution_id: UUID,
        event_type: WorkflowEventType,
        payload: dict,
        operator: str | None = None,
    ) -> None:
        event = WorkflowEvent(
            event_type=event_type,
            execution_id=execution_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            payload=payload,
            occurred_at=datetime.now(timezone.utc),
        )
        await self._events.emit(event)
        await self._audit.log_event(
            tenant_id=tenant_id, agent_id=agent_id, event=event, operator=operator,
        )
