"""Policy engine tests."""

from app.workflow.policy.policy_engine import PolicyEngine
from app.workflow.schemas import BusinessPolicyConfig


def test_blocked_tool_violation():
    engine = PolicyEngine()
    policy = BusinessPolicyConfig(blocked_tools=["refund_processor"])
    violations = engine.evaluate(policy, {"tool_slug": "refund_processor"})
    assert any("blocked_tool" in v for v in violations)


def test_max_refund_exceeded():
    engine = PolicyEngine()
    policy = BusinessPolicyConfig(max_refund=500)
    violations = engine.evaluate(policy, {"refund_amount": 750})
    assert any("max_refund_exceeded" in v for v in violations)


def test_vip_detection():
    engine = PolicyEngine()
    policy = BusinessPolicyConfig(vip_rules={"customer_ids": ["cust-123"]})
    assert engine.is_vip(policy, {"customer_id": "cust-123"})
    assert engine.is_vip(policy, {"customer_tier": "vip"})
    assert not engine.is_vip(policy, {"customer_id": "other"})


def test_allowed_tools_enforcement():
    engine = PolicyEngine()
    policy = BusinessPolicyConfig(allowed_tools=["appointment", "faq"])
    violations = engine.evaluate(policy, {"tool_slug": "refund"})
    assert any("tool_not_allowed" in v for v in violations)
