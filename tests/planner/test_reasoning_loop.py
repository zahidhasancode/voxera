"""Reasoning loop tests."""

from uuid import uuid4

from app.core.enums import PlannerAction, PlannerIntent, SessionState
from app.planner.reasoning.reasoning_loop import ReasoningLoop
from app.planner.schemas import OptimizedPlannerContext, PlannerInput


def _input(message: str, *, language: str = "en", tools=None):
    return PlannerInput(
        conversation_id=uuid4(),
        tenant_id=uuid4(),
        agent_id=uuid4(),
        current_user_message=message,
        current_state=SessionState.CALL_STARTED,
        language=language,
        available_tools=tools or [],
    )


def _context(message: str):
    return OptimizedPlannerContext(
        current_user_message=message,
        conversation_summary=None,
        working_memory={},
        retrieved_knowledge=[],
        tool_results=[],
        current_state=SessionState.CALL_STARTED,
        language="en",
        available_tool_slugs=[],
    )


def test_greeting_responds():
    loop = ReasoningLoop()
    plan = loop.evaluate(_context("Hello"), _input("Hello"), intent=PlannerIntent.GREETING, confidence=0.92)
    assert plan.action == PlannerAction.RESPOND
    assert plan.response


def test_emergency_transfers():
    loop = ReasoningLoop()
    plan = loop.evaluate(
        _context("Emergency help"),
        _input("Emergency help"),
        intent=PlannerIntent.EMERGENCY,
        confidence=0.95,
    )
    assert plan.action == PlannerAction.TRANSFER_HUMAN
    assert plan.tool_call is not None
    assert plan.tool_call.tool_slug == "human_transfer"


def test_general_question_retrieves():
    loop = ReasoningLoop()
    plan = loop.evaluate(
        _context("What is your refund policy?"),
        _input("What is your refund policy?"),
        intent=PlannerIntent.GENERAL_QUESTION,
        confidence=0.75,
    )
    assert plan.action == PlannerAction.RETRIEVE
    assert plan.retrieval_query


def test_multilingual_greeting():
    loop = ReasoningLoop()
    plan = loop.evaluate(
        _context("Hola"),
        _input("Hola", language="es"),
        intent=PlannerIntent.GREETING,
        confidence=0.92,
    )
    assert "ayudarle" in (plan.response or "").lower() or "hola" in (plan.response or "").lower()
