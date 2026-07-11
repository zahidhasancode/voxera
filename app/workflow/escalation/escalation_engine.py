"""Escalation engine with context preservation."""

from uuid import uuid4

from app.core.enums import EscalationTarget, WorkflowEventType, WorkflowExecutionStatus, WorkflowState
from app.workflow.schemas import WorkflowStepResult


class EscalationEngine:
    """Escalates to human, supervisor, department, emergency queue, or notifications."""

    def escalate(
        self,
        *,
        target: EscalationTarget | str,
        reason: str,
        context_snapshot: dict,
        escalation_policy: dict | None = None,
    ) -> tuple[WorkflowStepResult, dict]:
        target_str = target.value if hasattr(target, "value") else str(target)
        policy = escalation_policy or {}

        record = {
            "id": uuid4(),
            "target": target_str,
            "reason": reason,
            "context_snapshot": self._build_snapshot(context_snapshot),
            "status": "pending",
            "notify_channels": policy.get("notify_channels", []),
        }

        if target_str == EscalationTarget.EMERGENCY_QUEUE:
            record["priority"] = "critical"

        return (
            WorkflowStepResult(
                state=WorkflowState.ESCALATED,
                status=WorkflowExecutionStatus.ESCALATED,
                actions_taken=[f"escalated_to:{target_str}"],
                escalation_id=record["id"],
                completed=False,
                message=reason,
                events=[WorkflowEventType.WORKFLOW_ESCALATED],
            ),
            record,
        )

    def _build_snapshot(self, context: dict) -> dict:
        return {
            "conversation_id": str(context.get("conversation_id", "")),
            "working_memory": context.get("working_memory", {}),
            "conversation_summary": context.get("conversation_summary"),
            "tool_results": context.get("tool_results", []),
            "planner_output": context.get("planner_output"),
            "verifier_result": context.get("verifier_result"),
            "reasoning_summary": context.get("reasoning_summary"),
        }
