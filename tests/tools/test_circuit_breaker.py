"""Circuit breaker tests."""

import pytest

from app.core.exceptions import ToolCircuitOpenError
from app.tools.execution.circuit_breaker import CircuitBreaker


def test_circuit_opens_after_threshold():
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=60)
    breaker.record_failure()
    breaker.record_failure()
    with pytest.raises(ToolCircuitOpenError):
        breaker.allow()


def test_circuit_resets_on_success():
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=60)
    breaker.record_failure()
    breaker.record_success()
    breaker.allow()
