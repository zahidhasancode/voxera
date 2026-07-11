"""Escalation engine tests."""

from app.core.enums import EscalationTarget, WorkflowState
from app.workflow.escalation.escalation_engine import EscalationEngine


def test_escalation_preserves_context():
    engine = EscalationEngine()
    context = {
        "conversation_id": "conv-1",
        "planner_output": {"intent": "emergency"},
        "verifier_result": {"approved": True},
        "working_memory": {"customer_name": "Jane"},
        "tool_results": [{"tool": "lookup"}],
        "reasoning_summary": "Emergency detected",
    }
    result, record = engine.escalate(
        target=EscalationTarget.EMERGENCY_QUEUE,
        reason="Healthcare emergency",
        context_snapshot=context,
    )
    assert result.state == WorkflowState.ESCALATED
    assert record["target"] == "emergency_queue"
    assert record["context_snapshot"]["planner_output"]["intent"] == "emergency"
    assert record["context_snapshot"]["working_memory"]["customer_name"] == "Jane"


def test_webhook_escalation():
    engine = EscalationEngine()
    result, record = engine.escalate(
        target=EscalationTarget.WEBHOOK,
        reason="Telecom outage",
        context_snapshot={"conversation_id": "c1"},
        escalation_policy={"notify_channels": ["webhook", "slack"]},
    )
    assert "escalated_to:webhook" in result.actions_taken
    assert record["notify_channels"] == ["webhook", "slack"]
