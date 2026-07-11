"""Golden dataset AI evaluation — planner intent accuracy."""

from __future__ import annotations

import pytest

from app.core.enums import PlannerIntent
from app.planner.reasoning.intent_engine import IntentEngine
from tests.datasets.loader import list_golden_domains, load_golden_dataset
from tests.utilities.evaluation import EvaluationCaseResult, build_report


@pytest.mark.e2e
@pytest.mark.parametrize("domain", list_golden_domains())
def test_golden_intent_accuracy(domain: str):
    dataset = load_golden_dataset(domain)
    engine = IntentEngine()
    results: list[EvaluationCaseResult] = []

    for case in dataset["cases"]:
        utterance = case["utterance"]
        expected = case["expected_intent"]
        intent, confidence = engine.classify(utterance)
        actual = intent.value if isinstance(intent, PlannerIntent) else str(intent)
        match = actual == expected
        results.append(
            EvaluationCaseResult(
                case_id=case["id"],
                domain=domain,
                passed=match,
                intent_match=match,
                intent_expected=expected,
                intent_actual=actual,
                notes=[] if match else [f"confidence={confidence:.2f}"],
            )
        )

    report = build_report(dataset["version"], domain, results)
    assert report.intent_accuracy >= 0.9, report.to_dict()
