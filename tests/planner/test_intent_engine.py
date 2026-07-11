"""Intent classification tests."""

from app.core.enums import PlannerIntent
from app.planner.reasoning.intent_engine import IntentEngine


def test_classify_greeting():
    engine = IntentEngine()
    intent, confidence = engine.classify("Hello there!")
    assert intent == PlannerIntent.GREETING
    assert confidence > 0.8


def test_classify_appointment():
    engine = IntentEngine()
    intent, confidence = engine.classify("I want to book an appointment for tomorrow")
    assert intent == PlannerIntent.APPOINTMENT
    assert confidence > 0.8


def test_classify_order_status():
    engine = IntentEngine()
    intent, _ = engine.classify("Where is my order?")
    assert intent == PlannerIntent.ORDER_STATUS


def test_classify_emergency():
    engine = IntentEngine()
    intent, confidence = engine.classify("This is an emergency!")
    assert intent == PlannerIntent.EMERGENCY
    assert confidence > 0.9


def test_classify_unknown_empty():
    engine = IntentEngine()
    intent, confidence = engine.classify("")
    assert intent == PlannerIntent.UNKNOWN
    assert confidence < 0.5
