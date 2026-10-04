"""Workflow observability metrics."""

from dataclasses import dataclass

from app.workflow.schemas import WorkflowMetricsSnapshot


@dataclass
class WorkflowMetricsCollector:
    total_executions: int = 0
    completed_count: int = 0
    failed_count: int = 0
    escalated_count: int = 0
    total_duration_ms: float = 0.0
    total_approval_time_ms: float = 0.0
    policy_violation_count: int = 0
    total_steps: int = 0
    total_wait_time_ms: float = 0.0

    def record_execution(
        self,
        *,
        completed: bool,
        failed: bool,
        escalated: bool,
        duration_ms: float,
        steps: int,
        policy_violations: int = 0,
        wait_ms: float = 0.0,
        approval_ms: float = 0.0,
    ) -> None:
        self.total_executions += 1
        self.total_duration_ms += duration_ms
        self.total_steps += steps
        self.total_wait_time_ms += wait_ms
        self.total_approval_time_ms += approval_ms
        self.policy_violation_count += policy_violations
        if completed:
            self.completed_count += 1
        if failed:
            self.failed_count += 1
        if escalated:
            self.escalated_count += 1

    def snapshot(self) -> WorkflowMetricsSnapshot:
        n = self.total_executions or 1
        return WorkflowMetricsSnapshot(
            total_executions=self.total_executions,
            completed_count=self.completed_count,
            failed_count=self.failed_count,
            escalated_count=self.escalated_count,
            average_duration_ms=self.total_duration_ms / n if self.total_executions else 0,
            average_approval_time_ms=self.total_approval_time_ms / n if self.total_executions else 0,
            escalation_rate=self.escalated_count / n if self.total_executions else 0,
            success_rate=self.completed_count / n if self.total_executions else 0,
            policy_violation_count=self.policy_violation_count,
            average_steps=self.total_steps / n if self.total_executions else 0,
            average_wait_time_ms=self.total_wait_time_ms / n if self.total_executions else 0,
        )
