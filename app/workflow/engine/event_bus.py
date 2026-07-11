"""In-process event bus for workflow events."""

from collections.abc import Awaitable, Callable
from typing import Any

from app.core.config import settings
from app.workflow.schemas import WorkflowEvent


class WorkflowEventBus:
    """Event-driven workflow notifications — Redis/Kafka-ready abstraction."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[WorkflowEvent], Awaitable[None]]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[WorkflowEvent], Awaitable[None]]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def emit(self, event: WorkflowEvent) -> None:
        if not settings.WORKFLOW_ENABLE_EVENT_BUS:
            return
        handlers = self._handlers.get(event.event_type.value, []) + self._handlers.get("*", [])
        for handler in handlers:
            await handler(event)
