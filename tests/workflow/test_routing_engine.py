"""Routing engine tests."""

from app.core.enums import RoutingStrategy, RuleOperator
from app.workflow.routing.routing_engine import RoutingEngine
from app.workflow.schemas import RuleCondition, RoutingRuleDefinition


def test_emergency_routing_overrides():
    engine = RoutingEngine()
    route = engine.route([], context={}, is_emergency=True)
    assert route["strategy"] == RoutingStrategy.EMERGENCY
    assert route["priority"] == "critical"


def test_vip_routing():
    engine = RoutingEngine()
    rules = [
        RoutingRuleDefinition(
            name="vip_queue",
            strategy=RoutingStrategy.VIP,
            conditions=[],
            target={"queue": "vip-priority", "priority": "high"},
        )
    ]
    route = engine.route(rules, context={}, is_vip=True)
    assert route["queue"] == "vip-priority"


def test_department_routing_by_condition():
    engine = RoutingEngine()
    rules = [
        RoutingRuleDefinition(
            name="billing",
            strategy=RoutingStrategy.DEPARTMENT,
            priority=10,
            conditions=[
                RuleCondition(field="department", operator=RuleOperator.EQ, value="billing")
            ],
            target={"queue": "billing", "department": "billing"},
        )
    ]
    route = engine.route(rules, context={"department": "billing"})
    assert route["department"] == "billing"
    assert route["strategy"] == RoutingStrategy.DEPARTMENT.value
