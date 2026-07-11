"""Approval engine tests."""

from uuid import uuid4

from app.core.enums import WorkflowExecutionStatus, WorkflowState
from app.workflow.approvals.approval_engine import ApprovalEngine


def test_auto_approve_empty_chain():
    engine = ApprovalEngine()
    result, pending = engine.evaluate(approval_chain=[], context={})
    assert result.state == WorkflowState.EXECUTING
    assert result.status == WorkflowExecutionStatus.RUNNING
    assert pending == []


def test_manager_approval_required():
    engine = ApprovalEngine()
    result, pending = engine.evaluate(
        approval_chain=[{"role": "supervisor", "mode": "manager"}],
        context={"refund_amount": 600},
    )
    assert result.state == WorkflowState.WAITING_APPROVAL
    assert result.requires_approval
    assert len(pending) == 1
    assert pending[0]["approver_role"] == "supervisor"


def test_two_step_approval_flow():
    engine = ApprovalEngine()
    _, pending = engine.evaluate(
        approval_chain=[
            {"role": "supervisor"},
            {"role": "finance"},
        ],
        context={},
    )
    first_id = pending[0]["id"]
    result, updated = engine.process_decision(approvals=pending, approval_id=first_id, approved=True)
    assert result.state == WorkflowState.WAITING_APPROVAL
    assert updated[0]["status"] == "approved"
    assert updated[1]["status"] == "pending"

    second_id = updated[1]["id"]
    result, updated = engine.process_decision(approvals=updated, approval_id=second_id, approved=True)
    assert result.state == WorkflowState.EXECUTING
    assert all(a["status"] == "approved" for a in updated)


def test_approval_rejection():
    engine = ApprovalEngine()
    approval_id = uuid4()
    pending = [{"id": approval_id, "status": "pending", "approver_role": "manager"}]
    result, _ = engine.process_decision(approvals=pending, approval_id=approval_id, approved=False)
    assert result.state == WorkflowState.REJECTED
    assert result.completed
