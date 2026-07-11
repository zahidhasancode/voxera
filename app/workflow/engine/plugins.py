"""Workflow action plugin registry."""

from abc import ABC, abstractmethod
from typing import Any

from app.workflow.schemas import WorkflowStepResult


class WorkflowActionPlugin(ABC):
    @abstractmethod
    def action_type(self) -> str:
        ...

    @abstractmethod
    async def execute(self, params: dict[str, Any], context: dict[str, Any]) -> WorkflowStepResult:
        ...


class NotifyActionPlugin(WorkflowActionPlugin):
    def action_type(self) -> str:
        return "notify"

    async def execute(self, params: dict[str, Any], context: dict[str, Any]) -> WorkflowStepResult:
        from app.core.enums import WorkflowExecutionStatus, WorkflowState

        return WorkflowStepResult(
            state=WorkflowState.EXECUTING,
            status=WorkflowExecutionStatus.RUNNING,
            actions_taken=[f"notify:{params.get('channel', 'default')}"],
        )


class CompleteActionPlugin(WorkflowActionPlugin):
    def action_type(self) -> str:
        return "complete"

    async def execute(self, params: dict[str, Any], context: dict[str, Any]) -> WorkflowStepResult:
        from app.core.enums import WorkflowEventType, WorkflowExecutionStatus, WorkflowState

        return WorkflowStepResult(
            state=WorkflowState.COMPLETED,
            status=WorkflowExecutionStatus.COMPLETED,
            actions_taken=["workflow_completed"],
            completed=True,
            events=[WorkflowEventType.WORKFLOW_COMPLETED],
        )


class WorkflowPluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, WorkflowActionPlugin] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        for plugin in (NotifyActionPlugin(), CompleteActionPlugin()):
            self.register(plugin)

    def register(self, plugin: WorkflowActionPlugin) -> None:
        self._plugins[plugin.action_type()] = plugin

    def get(self, action_type: str) -> WorkflowActionPlugin | None:
        return self._plugins.get(action_type)

    async def execute_action(self, action_type: str, params: dict, context: dict) -> WorkflowStepResult | None:
        plugin = self.get(action_type)
        if plugin is None:
            return None
        return await plugin.execute(params, context)
