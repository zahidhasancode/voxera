"""Structured conversation summarizer."""

import re
import time
from abc import ABC, abstractmethod

from app.core.logger import get_logger
from app.memory.schemas import StructuredSummary, TurnRead

logger = get_logger(__name__)

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
_ORDER = re.compile(r"(?:order|reference|confirmation)\s*(?:#|number)?\s*([A-Z0-9-]{4,})", re.I)


class ConversationSummarizer(ABC):
    @abstractmethod
    async def summarize(self, turns: list[TurnRead], *, language: str = "en") -> StructuredSummary:
        raise NotImplementedError


class StructuredConversationSummarizer(ConversationSummarizer):
    """
    Rule-based structured summarizer — production-safe without LLM dependency.

    Extracts identity signals, goals, resolved/pending items from turns.
    Replace with LLM summarizer via DI when configured.
    """

    _GOAL_PATTERNS = [
        re.compile(r"(?:i want to|i need to|help me|can you|looking to)\s+(.{5,80})", re.I),
        re.compile(r"(?:question about|issue with|problem with)\s+(.{5,80})", re.I),
    ]
    _RESOLVED_PATTERNS = [
        re.compile(r"(?:that works|thank you|got it|resolved|confirmed|all set)", re.I),
    ]
    _PENDING_PATTERNS = [
        re.compile(r"(?:still need|waiting for|not yet|pending|follow up)", re.I),
    ]

    async def summarize(self, turns: list[TurnRead], *, language: str = "en") -> StructuredSummary:
        started = time.monotonic()
        collected: dict[str, str] = {}
        customer_identity = None
        conversation_goal = None
        resolved: list[str] = []
        pending: list[str] = []

        for turn in turns:
            text = turn.message.strip()
            if turn.role.value == "user":
                if not customer_identity:
                    customer_identity = self._extract_identity(text)
                if not conversation_goal:
                    conversation_goal = self._extract_goal(text)
                for key, val in self._extract_collected(text).items():
                    collected.setdefault(key, val)
                if any(p.search(text) for p in self._PENDING_PATTERNS):
                    pending.append(self._truncate(text))
                elif any(p.search(text) for p in self._RESOLVED_PATTERNS):
                    resolved.append(self._truncate(text))

            if turn.role.value == "assistant" and "verified" in text.lower():
                collected["verification_status"] = "verified"

        summary_text = self._format_summary(
            customer_identity, conversation_goal, resolved, pending, collected
        )
        token_estimate = max(1, len(summary_text) // 4)
        elapsed_ms = int((time.monotonic() - started) * 1000)

        logger.info(
            "Summary generated",
            extra_fields={
                "turn_count": len(turns),
                "token_estimate": token_estimate,
                "duration_ms": elapsed_ms,
                "event": "memory_summary_generated",
            },
        )

        return StructuredSummary(
            customer_identity=customer_identity,
            conversation_goal=conversation_goal,
            resolved_items=resolved[:10],
            pending_items=pending[:10],
            collected_information=collected,
            summary_text=summary_text,
            token_estimate=token_estimate,
            language=language,
        )

    def _extract_identity(self, text: str) -> str | None:
        if _EMAIL.search(text):
            return "Customer provided email"
        if _PHONE.search(text):
            return "Customer provided phone"
        match = re.search(r"(?:my name is|i am|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text, re.I)
        return match.group(1).strip() if match else None

    def _extract_goal(self, text: str) -> str | None:
        for pattern in self._GOAL_PATTERNS:
            match = pattern.search(text)
            if match:
                return self._truncate(match.group(1).strip())
        return self._truncate(text) if len(text) > 20 else None

    def _extract_collected(self, text: str) -> dict[str, str]:
        result: dict[str, str] = {}
        email = _EMAIL.search(text)
        if email:
            result["email"] = email.group(0)
        phone = _PHONE.search(text)
        if phone:
            result["phone"] = phone.group(0).strip()
        order = _ORDER.search(text)
        if order:
            result["order_number"] = order.group(1)
        return result

    @staticmethod
    def _truncate(text: str, max_len: int = 120) -> str:
        return text if len(text) <= max_len else text[: max_len - 3] + "..."

    @staticmethod
    def _format_summary(
        identity: str | None,
        goal: str | None,
        resolved: list[str],
        pending: list[str],
        collected: dict,
    ) -> str:
        parts = ["## Conversation Summary"]
        if identity:
            parts.append(f"Customer Identity: {identity}")
        if goal:
            parts.append(f"Conversation Goal: {goal}")
        if resolved:
            parts.append("Resolved Items:\n- " + "\n- ".join(resolved))
        if pending:
            parts.append("Pending Items:\n- " + "\n- ".join(pending))
        if collected:
            items = [f"{k}: {v}" for k, v in collected.items()]
            parts.append("Collected Information:\n- " + "\n- ".join(items))
        return "\n\n".join(parts)
