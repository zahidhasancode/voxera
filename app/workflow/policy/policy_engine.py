"""Tenant policy configuration engine."""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.workflow.schemas import BusinessPolicyConfig


class PolicyEngine:
    """Loads and evaluates tenant business policies — nothing hardcoded."""

    def merge_policies(self, policies: list[dict[str, Any]]) -> BusinessPolicyConfig:
        merged: dict[str, Any] = {}
        for p in policies:
            if not p.get("enabled", True):
                continue
            value = p.get("policy_value") or {}
            if isinstance(value, dict):
                merged.update(value)
        return BusinessPolicyConfig.model_validate(merged)

    def evaluate(self, policy: BusinessPolicyConfig, context: dict[str, Any]) -> list[str]:
        violations: list[str] = []

        if policy.blocked_tools:
            tool = context.get("tool_slug") or context.get("planner", {}).get("tool_call", {}).get("tool_slug")
            if tool and tool in policy.blocked_tools:
                violations.append(f"blocked_tool:{tool}")

        if policy.allowed_tools:
            tool = context.get("tool_slug")
            if tool and tool not in policy.allowed_tools:
                violations.append(f"tool_not_allowed:{tool}")

        amount = self._numeric(context.get("refund_amount") or context.get("amount"))
        if policy.max_refund is not None and amount > policy.max_refund:
            violations.append(f"max_refund_exceeded:{amount}>{policy.max_refund}")

        discount = self._numeric(context.get("discount_amount"))
        if policy.max_discount is not None and discount > policy.max_discount:
            violations.append(f"max_discount_exceeded:{discount}>{policy.max_discount}")

        if policy.languages and context.get("language") not in policy.languages:
            violations.append(f"language_not_allowed:{context.get('language')}")

        if not self._within_working_hours(policy):
            if context.get("intent") == "appointment" or context.get("tool_slug") == "appointment":
                violations.append("outside_working_hours")

        confidence = self._numeric(context.get("confidence") or context.get("planner", {}).get("confidence"))
        if policy.escalation_threshold is not None and confidence < policy.escalation_threshold:
            violations.append("confidence_below_escalation_threshold")

        return violations

    def is_vip(self, policy: BusinessPolicyConfig, context: dict[str, Any]) -> bool:
        vip_rules = policy.vip_rules or {}
        if context.get("customer_tier") == "vip":
            return True
        if context.get("customer_id") in vip_rules.get("customer_ids", []):
            return True
        return bool(context.get("working_memory", {}).get("vip") == "true")

    def _within_working_hours(self, policy: BusinessPolicyConfig) -> bool:
        if not policy.working_hours_start or not policy.working_hours_end:
            return True
        try:
            tz = ZoneInfo(policy.timezone)
        except Exception:
            tz = ZoneInfo("UTC")
        now = datetime.now(tz).strftime("%H:%M")
        today = datetime.now(tz).strftime("%Y-%m-%d")
        if today in policy.holidays:
            return False
        return policy.working_hours_start <= now <= policy.working_hours_end

    def _numeric(self, value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0
