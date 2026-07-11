"""Context optimizer tests."""

from uuid import uuid4

from app.core.enums import SessionState
from app.planner.schemas import PlannerInput
from app.planner.state.context_optimizer import ContextOptimizer


def test_optimizer_limits_knowledge():
    optimizer = ContextOptimizer()
    planner_input = PlannerInput(
        conversation_id=uuid4(),
        tenant_id=uuid4(),
        agent_id=uuid4(),
        current_user_message="test",
        retrieved_knowledge=[f"chunk-{i}" for i in range(20)],
        current_state=SessionState.CALL_STARTED,
    )
    optimized = optimizer.optimize(planner_input)
    assert len(optimized.retrieved_knowledge) <= 8


def test_optimizer_token_estimate():
    optimizer = ContextOptimizer()
    planner_input = PlannerInput(
        conversation_id=uuid4(),
        tenant_id=uuid4(),
        agent_id=uuid4(),
        current_user_message="x" * 1000,
        current_state=SessionState.CALL_STARTED,
    )
    optimized = optimizer.optimize(planner_input)
    assert optimized.token_estimate > 0
