"""Extensible intent classification engine."""

import re
from dataclasses import dataclass

from app.core.enums import PlannerIntent


@dataclass(frozen=True)
class IntentPattern:
    intent: PlannerIntent
    patterns: tuple[re.Pattern[str], ...]
    base_confidence: float = 0.85


class IntentEngine:
    """Rule-based intent registry — new intents require no Planner rewrite."""

    def __init__(self) -> None:
        self._patterns: list[IntentPattern] = [
            IntentPattern(
                PlannerIntent.GREETING,
                (re.compile(r"\b(hi|hello|hey|good morning|good afternoon|good evening)\b", re.I),),
                0.92,
            ),
            IntentPattern(
                PlannerIntent.EMERGENCY,
                (re.compile(r"\b(emergency|urgent|911|help me now|life threatening)\b", re.I),),
                0.95,
            ),
            IntentPattern(
                PlannerIntent.APPOINTMENT,
                (
                    re.compile(r"\b(book|schedule|reschedule|cancel)\b.*\b(appointment|meeting)\b", re.I),
                    re.compile(r"\bappointment\b", re.I),
                ),
                0.90,
            ),
            IntentPattern(
                PlannerIntent.ORDER_STATUS,
                (
                    re.compile(r"\b(order|package|delivery|tracking|shipment)\b", re.I),
                    re.compile(r"\bwhere is my order\b", re.I),
                ),
                0.88,
            ),
            IntentPattern(
                PlannerIntent.REFUND,
                (re.compile(r"\b(refund|money back|return item)\b", re.I),),
                0.87,
            ),
            IntentPattern(
                PlannerIntent.CANCEL_SUBSCRIPTION,
                (re.compile(r"\b(cancel subscription|unsubscribe|stop billing)\b", re.I),),
                0.86,
            ),
            IntentPattern(
                PlannerIntent.TECHNICAL_ISSUE,
                (
                    re.compile(r"\b(not working|broken|error|bug|issue|problem)\b", re.I),
                    re.compile(r"\btroubleshoot\b", re.I),
                ),
                0.84,
            ),
            IntentPattern(
                PlannerIntent.COMPLAINT,
                (re.compile(r"\b(complaint|unhappy|frustrated|terrible service|manager)\b", re.I),),
                0.83,
            ),
            IntentPattern(
                PlannerIntent.IDENTITY_VERIFICATION,
                (
                    re.compile(r"\b(verify|verification|otp|confirm identity|authenticate)\b", re.I),
                    re.compile(r"\bmy email is\b", re.I),
                ),
                0.82,
            ),
            IntentPattern(
                PlannerIntent.GENERAL_QUESTION,
                (re.compile(r"\b(what|how|when|where|why|can you tell me)\b", re.I),),
                0.70,
            ),
        ]

    def classify(self, message: str | None, *, language: str = "en") -> tuple[PlannerIntent, float]:
        if not message or not message.strip():
            return PlannerIntent.UNKNOWN, 0.30

        best_intent = PlannerIntent.UNKNOWN
        best_confidence = 0.35

        for entry in self._patterns:
            for pattern in entry.patterns:
                if pattern.search(message):
                    if entry.base_confidence > best_confidence:
                        best_intent = entry.intent
                        best_confidence = entry.base_confidence
                    break

        if language != "en" and best_intent == PlannerIntent.UNKNOWN:
            best_confidence = max(best_confidence, 0.45)

        return best_intent, min(best_confidence, 0.98)

    def register(self, pattern: IntentPattern) -> None:
        self._patterns.append(pattern)
