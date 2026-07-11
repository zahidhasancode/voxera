"""Routing engine for department, skill, language, VIP, emergency."""

from app.core.enums import RoutingStrategy
from app.workflow.rules.rule_engine import RuleEngine
from app.workflow.schemas import RoutingRuleDefinition


class RoutingEngine:
    def __init__(self, rule_engine: RuleEngine | None = None) -> None:
        self._rules = rule_engine or RuleEngine()

    def route(
        self,
        routing_rules: list[RoutingRuleDefinition],
        context: dict,
        *,
        is_vip: bool = False,
        is_emergency: bool = False,
    ) -> dict | None:
        if is_emergency:
            return {"strategy": RoutingStrategy.EMERGENCY, "queue": "emergency", "priority": "critical"}

        if is_vip:
            vip_rule = next((r for r in routing_rules if r.strategy == RoutingStrategy.VIP and r.enabled), None)
            if vip_rule:
                return vip_rule.target

        sorted_rules = sorted([r for r in routing_rules if r.enabled], key=lambda r: r.priority)
        for rule in sorted_rules:
            if self._rules.match_conditions(rule.conditions, context):
                return {**rule.target, "strategy": rule.strategy.value}

        return {"strategy": RoutingStrategy.ROUND_ROBIN, "queue": "default", "priority": "normal"}
