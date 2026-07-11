"""Rule engine tests."""

from app.core.enums import RuleActionType, RuleOperator
from app.workflow.rules.rule_engine import RuleEngine
from app.workflow.schemas import RuleAction, RuleCondition, WorkflowRuleDefinition


def test_refund_over_threshold_requires_approval():
    engine = RuleEngine()
    rules = [
        WorkflowRuleDefinition(
            name="high_refund",
            priority=10,
            conditions=[RuleCondition(field="refund_amount", operator=RuleOperator.GT, value=500)],
            actions=[RuleAction(type=RuleActionType.REQUIRE_APPROVAL, params={"role": "manager"})],
        )
    ]
    actions = engine.evaluate(rules, {"refund_amount": 750})
    assert len(actions) == 1
    assert actions[0].type == RuleActionType.REQUIRE_APPROVAL


def test_vip_customer_routes_priority():
    engine = RuleEngine()
    rules = [
        WorkflowRuleDefinition(
            name="vip",
            priority=5,
            conditions=[RuleCondition(field="customer_tier", operator=RuleOperator.EQ, value="vip")],
            actions=[RuleAction(type=RuleActionType.ROUTE, params={"queue": "vip"})],
        )
    ]
    actions = engine.evaluate(rules, {"customer_tier": "vip"})
    assert actions[0].type == RuleActionType.ROUTE


def test_else_action_when_no_match():
    engine = RuleEngine()
    rules = [
        WorkflowRuleDefinition(
            name="default",
            priority=100,
            conditions=[RuleCondition(field="amount", operator=RuleOperator.GT, value=10000)],
            actions=[RuleAction(type=RuleActionType.REJECT, params={})],
            else_actions=[RuleAction(type=RuleActionType.COMPLETE, params={})],
        )
    ]
    actions = engine.evaluate(rules, {"amount": 50})
    assert actions[0].type == RuleActionType.COMPLETE


def test_nested_field_resolution():
    engine = RuleEngine()
    rules = [
        WorkflowRuleDefinition(
            name="planner_intent",
            priority=10,
            conditions=[
                RuleCondition(field="planner_output.intent", operator=RuleOperator.EQ, value="emergency")
            ],
            actions=[RuleAction(type=RuleActionType.ESCALATE, params={"target": "emergency_queue"})],
        )
    ]
    actions = engine.evaluate(rules, {"planner_output": {"intent": "emergency"}})
    assert actions[0].type == RuleActionType.ESCALATE
