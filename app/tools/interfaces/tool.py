"""Enterprise tool interface — every tool implements this contract."""

from abc import ABC, abstractmethod
from typing import Any

from app.tools.schemas.execution import ToolExecutionContext, ToolExecutionResult


class Tool(ABC):
    """Plugin interface for VOXERA tools."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable tool name."""

    @abstractmethod
    def slug(self) -> str:
        """Unique tool identifier (registry key)."""

    @abstractmethod
    def description(self) -> str:
        """Description for Planner tool selection."""

    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema for tool arguments."""

    @abstractmethod
    def permission_scope(self) -> str:
        """Permission category (e.g. appointment, crm, communication)."""

    @abstractmethod
    async def execute(self, context: ToolExecutionContext) -> dict[str, Any]:
        """Execute tool logic; return structured result payload."""

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Health check for external dependencies."""

    @abstractmethod
    async def validate(self, arguments: dict[str, Any]) -> list[str]:
        """Validate arguments; return list of violation messages (empty = valid)."""
