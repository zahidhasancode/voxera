"""Performance smoke tests against SLO targets."""

from __future__ import annotations

import pytest

from tests.utilities.benchmarks import BenchmarkReport, SLO, measure_latency


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_health_live_latency_slo(http_client):
    report = BenchmarkReport()
    for _ in range(10):
        with measure_latency(report, "health_live"):
            response = await http_client.get("/api/v1/health/live")
        assert response.status_code == 200
    assert report.p95("health_live") <= SLO["health_live"] * 3


@pytest.mark.benchmark
def test_planner_intent_classification_latency():
    from app.planner.reasoning.intent_engine import IntentEngine

    engine = IntentEngine()
    report = BenchmarkReport()
    for _ in range(20):
        with measure_latency(report, "planner_intent_classify"):
            engine.classify("I want to book an appointment tomorrow")
    assert report.p95("planner_intent_classify") <= SLO["planner_intent_classify"] * 5


@pytest.mark.benchmark
def test_verifier_hallucination_check_latency():
    from uuid import uuid4

    from app.core.enums import PlannerAction, PlannerIntent, SessionState
    from app.planner.schemas import ExecutionPlan, PlannerPlan
    from app.verifier.schemas import ValidationContext, VerifierInput
    from app.verifier.validators.hallucination_detector import HallucinationDetector

    plan = PlannerPlan(
        intent=PlannerIntent.GENERAL_QUESTION,
        confidence=0.9,
        reasoning=["test"],
        next_action="respond",
        action=PlannerAction.RESPOND,
        response="Hello, how can I help?",
        plan=ExecutionPlan(goal="assist"),
    )
    ctx = ValidationContext(
        verifier_input=VerifierInput(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            agent_id=uuid4(),
            planner_output=plan,
            current_state=SessionState.CALL_STARTED,
        )
    )
    ctx.known_intents = {PlannerIntent.GENERAL_QUESTION.value}
    detector = HallucinationDetector()
    report = BenchmarkReport()
    for _ in range(20):
        with measure_latency(report, "verifier_pipeline"):
            detector.validate(ctx)
    assert report.p95("verifier_pipeline") <= SLO["verifier_pipeline"] * 5
