"""Configurable IF/THEN/ELSE rule engine."""

from typing import Any

from app.core.enums import RuleOperator
from app.workflow.schemas import RuleAction, RuleCondition, WorkflowRuleDefinition


class RuleEngine:
    """Evaluates tenant-configurable business rules against workflow context."""

    def evaluate(self, rules: list[WorkflowRuleDefinition], context: dict[str, Any]) -> list[RuleAction]:
        matched: list[RuleAction] = []
        sorted_rules = sorted(
            [r for r in rules if r.enabled],
            key=lambda r: r.priority,
        )
        for rule in sorted_rules:
            if self._match_all(rule.conditions, context):
                matched.extend(rule.actions)
            elif rule.else_actions:
                matched.extend(rule.else_actions)
        return matched

    def match_conditions(self, conditions: list[RuleCondition], context: dict[str, Any]) -> bool:
        return all(self._match_one(c, context) for c in conditions)

    def _match_all(self, conditions: list[RuleCondition], context: dict[str, Any]) -> bool:
        return self.match_conditions(conditions, context)

    def _match_one(self, condition: RuleCondition, context: dict[str, Any]) -> bool:
        actual = self._resolve_field(condition.field, context)
        expected = condition.value
        op = condition.operator

        if op == RuleOperator.EQ:
            return actual == expected
        if op == RuleOperator.NE:
            return actual != expected
        if op == RuleOperator.GT:
            return self._numeric(actual) > self._numeric(expected)
        if op == RuleOperator.GTE:
            return self._numeric(actual) >= self._numeric(expected)
        if op == RuleOperator.LT:
            return self._numeric(actual) < self._numeric(expected)
        if op == RuleOperator.LTE:
            return self._numeric(actual) <= self._numeric(expected)
        if op == RuleOperator.IN:
            return actual in (expected if isinstance(expected, list) else [expected])
        if op == RuleOperator.NOT_IN:
            return actual not in (expected if isinstance(expected, list) else [expected])
        if op == RuleOperator.CONTAINS:
            return str(expected).lower() in str(actual).lower()
        return False

    def _resolve_field(self, field: str, context: dict[str, Any]) -> Any:
        parts = field.split(".")
        value: Any = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _numeric(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
