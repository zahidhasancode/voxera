"""Approval chain engine."""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.enums import (
    WorkflowApprovalMode,
    WorkflowApprovalStatus,
    WorkflowExecutionStatus,
    WorkflowState,
)
from app.workflow.schemas import WorkflowStepResult


class ApprovalEngine:
    """Manages auto, manager, department, two-step, and time-limited approvals."""

    def evaluate(
        self,
        *,
        approval_chain: list[dict],
        context: dict,
        auto_approve: bool = False,
    ) -> tuple[WorkflowStepResult, list[dict]]:
        if auto_approve or not approval_chain:
            return (
                WorkflowStepResult(
                    state=WorkflowState.EXECUTING,
                    status=WorkflowExecutionStatus.RUNNING,
                    actions_taken=["auto_approved"],
                    completed=False,
                ),
                [],
            )

        pending: list[dict] = []
        now = datetime.now(timezone.utc)
        for idx, step in enumerate(approval_chain):
            mode = step.get("mode", WorkflowApprovalMode.MANAGER)
            pending.append(
                {
                    "id": uuid4(),
                    "approval_mode": mode.value if hasattr(mode, "value") else str(mode),
                    "status": WorkflowApprovalStatus.PENDING.value,
                    "approver_role": step.get("role"),
                    "step_order": idx,
                    "reason": step.get("reason"),
                    "expires_at": now + timedelta(seconds=step.get("timeout_seconds", settings.WORKFLOW_APPROVAL_TIMEOUT_SECONDS)),
                }
            )

        first = pending[0]
        return (
            WorkflowStepResult(
                state=WorkflowState.WAITING_APPROVAL,
                status=WorkflowExecutionStatus.PAUSED,
                actions_taken=["approval_required"],
                requires_approval=True,
                approval_id=first["id"],
                message=f"Awaiting {first.get('approver_role', 'approver')} approval",
            ),
            pending,
        )

    def process_decision(
        self,
        *,
        approvals: list[dict],
        approval_id: UUID,
        approved: bool,
    ) -> tuple[WorkflowStepResult, list[dict]]:
        updated = []
        all_done = True
        for a in approvals:
            if str(a.get("id")) == str(approval_id):
                a["status"] = WorkflowApprovalStatus.APPROVED.value if approved else WorkflowApprovalStatus.REJECTED.value
                a["decided_at"] = datetime.now(timezone.utc).isoformat()
            updated.append(a)
            if a.get("status") == WorkflowApprovalStatus.PENDING.value:
                all_done = False

        if not approved:
            return (
                WorkflowStepResult(
                    state=WorkflowState.REJECTED,
                    status=WorkflowExecutionStatus.REJECTED,
                    actions_taken=["approval_rejected"],
                    completed=True,
                    message="Approval rejected",
                ),
                updated,
            )

        if all_done:
            return (
                WorkflowStepResult(
                    state=WorkflowState.EXECUTING,
                    status=WorkflowExecutionStatus.RUNNING,
                    actions_taken=["all_approvals_granted"],
                    completed=False,
                ),
                updated,
            )

        next_pending = next(a for a in updated if a.get("status") == WorkflowApprovalStatus.PENDING.value)
        return (
            WorkflowStepResult(
                state=WorkflowState.WAITING_APPROVAL,
                status=WorkflowExecutionStatus.PAUSED,
                requires_approval=True,
                approval_id=next_pending["id"],
                message="Awaiting next approval step",
            ),
            updated,
        )
