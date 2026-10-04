"""IAM metrics collector."""

from dataclasses import dataclass

from app.iam.schemas import IamMetricsSnapshot


@dataclass
class IamMetricsCollector:
    login_success_count: int = 0
    login_failure_count: int = 0
    permission_checks: int = 0
    policy_violations: int = 0
    security_alerts: int = 0
    api_key_usage_count: int = 0

    def record_login(self, *, success: bool) -> None:
        if success:
            self.login_success_count += 1
        else:
            self.login_failure_count += 1

    def record_permission_check(self) -> None:
        self.permission_checks += 1

    def snapshot(self, *, active_sessions: int = 0) -> IamMetricsSnapshot:
        return IamMetricsSnapshot(
            login_success_count=self.login_success_count,
            login_failure_count=self.login_failure_count,
            active_sessions=active_sessions,
            api_key_usage_count=self.api_key_usage_count,
            permission_checks=self.permission_checks,
            security_alerts=self.security_alerts,
            policy_violations=self.policy_violations,
        )
