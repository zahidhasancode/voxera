"""Business hours, timezone, and holiday scheduler."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.workflow.schemas import BusinessPolicyConfig


class WorkflowScheduler:
    """Evaluates whether actions are allowed at current time."""

    def is_within_business_hours(self, policy: BusinessPolicyConfig) -> bool:
        if not policy.working_hours_start or not policy.working_hours_end:
            return True
        try:
            tz = ZoneInfo(policy.timezone)
        except Exception:
            tz = ZoneInfo("UTC")
        now = datetime.now(tz)
        if now.strftime("%Y-%m-%d") in policy.holidays:
            return False
        current = now.strftime("%H:%M")
        return policy.working_hours_start <= current <= policy.working_hours_end

    def can_execute_now(self, policy: BusinessPolicyConfig, *, allow_delayed: bool = True) -> tuple[bool, str | None]:
        if self.is_within_business_hours(policy):
            return True, None
        if allow_delayed:
            return False, "delayed_until_business_hours"
        return False, "outside_business_hours"

    def next_execution_window(self, policy: BusinessPolicyConfig) -> str | None:
        if self.is_within_business_hours(policy):
            return None
        return policy.working_hours_start
