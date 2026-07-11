"""Circuit breaker for external API tools."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.enums import CircuitBreakerState
from app.core.exceptions import ToolCircuitOpenError


@dataclass
class CircuitBreaker:
    failure_threshold: int = field(default_factory=lambda: settings.TOOL_CIRCUIT_FAILURE_THRESHOLD)
    recovery_seconds: int = field(default_factory=lambda: settings.TOOL_CIRCUIT_RECOVERY_SECONDS)
    failure_count: int = 0
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    opened_at: datetime | None = None

    def allow(self) -> None:
        if self.state == CircuitBreakerState.OPEN:
            if self.opened_at and datetime.now(timezone.utc) - self.opened_at >= timedelta(
                seconds=self.recovery_seconds
            ):
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise ToolCircuitOpenError("Circuit breaker is open", retryable=True)

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.opened_at = None

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.opened_at = datetime.now(timezone.utc)


class CircuitBreakerRegistry:
    """Per-tenant-per-tool circuit breakers (in-process; Redis-ready)."""

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(self, key: str) -> CircuitBreaker:
        if key not in self._breakers:
            self._breakers[key] = CircuitBreaker()
        return self._breakers[key]
