"""Scheduler tests."""

from app.workflow.scheduler.scheduler import WorkflowScheduler
from app.workflow.schemas import BusinessPolicyConfig


def test_business_hours_within_range():
    scheduler = WorkflowScheduler()
    policy = BusinessPolicyConfig(
        working_hours_start="00:00",
        working_hours_end="23:59",
        timezone="UTC",
    )
    assert scheduler.is_within_business_hours(policy)


def test_holiday_blocks_execution():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    scheduler = WorkflowScheduler()
    today = datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%d")
    policy = BusinessPolicyConfig(
        working_hours_start="00:00",
        working_hours_end="23:59",
        timezone="UTC",
        holidays=[today],
    )
    assert not scheduler.is_within_business_hours(policy)


def test_can_execute_now_outside_hours():
    scheduler = WorkflowScheduler()
    policy = BusinessPolicyConfig(
        working_hours_start="03:00",
        working_hours_end="04:00",
        timezone="UTC",
    )
    can_exec, reason = scheduler.can_execute_now(policy, allow_delayed=True)
    if not scheduler.is_within_business_hours(policy):
        assert can_exec is False
        assert reason == "delayed_until_business_hours"
