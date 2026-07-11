"""Configurable permission catalog and system role definitions."""

from app.core.enums import IamPermission, SystemRole

PERMISSION_CATALOG: dict[str, dict[str, str]] = {
    IamPermission.VIEW_CALLS: {"name": "View Calls", "category": "calls"},
    IamPermission.DELETE_CALLS: {"name": "Delete Calls", "category": "calls"},
    IamPermission.MANAGE_AGENTS: {"name": "Manage Agents", "category": "agents"},
    IamPermission.MANAGE_KNOWLEDGE: {"name": "Manage Knowledge", "category": "knowledge"},
    IamPermission.MANAGE_BILLING: {"name": "Manage Billing", "category": "billing"},
    IamPermission.VIEW_AUDIT_LOGS: {"name": "View Audit Logs", "category": "audit"},
    IamPermission.EXECUTE_TOOLS: {"name": "Execute Tools", "category": "tools"},
    IamPermission.APPROVE_WORKFLOWS: {"name": "Approve Workflows", "category": "workflows"},
    IamPermission.MANAGE_USERS: {"name": "Manage Users", "category": "users"},
    IamPermission.MANAGE_API_KEYS: {"name": "Manage API Keys", "category": "security"},
    IamPermission.MANAGE_ROLES: {"name": "Manage Roles", "category": "security"},
    IamPermission.MANAGE_SECURITY: {"name": "Manage Security", "category": "security"},
    IamPermission.MANAGE_ORGANIZATION: {"name": "Manage Organization", "category": "organization"},
    IamPermission.VIEW_ANALYTICS: {"name": "View Analytics", "category": "analytics"},
}

ALL_PERMISSIONS = frozenset(PERMISSION_CATALOG.keys())

SYSTEM_ROLE_INHERITANCE: dict[str, list[str]] = {
    SystemRole.OWNER: [],
    SystemRole.ADMINISTRATOR: [SystemRole.OWNER],
    SystemRole.SUPERVISOR: [SystemRole.MANAGER],
    SystemRole.MANAGER: [SystemRole.AGENT],
    SystemRole.AGENT: [SystemRole.VIEWER],
    SystemRole.DEVELOPER: [SystemRole.VIEWER],
    SystemRole.BILLING: [SystemRole.VIEWER],
    SystemRole.SECURITY_AUDITOR: [SystemRole.VIEWER],
    SystemRole.VIEWER: [],
}

SYSTEM_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    SystemRole.OWNER: ALL_PERMISSIONS,
    SystemRole.ADMINISTRATOR: ALL_PERMISSIONS - frozenset({IamPermission.MANAGE_ORGANIZATION}),
    SystemRole.SUPERVISOR: frozenset(
        {
            IamPermission.VIEW_CALLS,
            IamPermission.MANAGE_AGENTS,
            IamPermission.EXECUTE_TOOLS,
            IamPermission.APPROVE_WORKFLOWS,
            IamPermission.VIEW_AUDIT_LOGS,
            IamPermission.VIEW_ANALYTICS,
            IamPermission.MANAGE_KNOWLEDGE,
        }
    ),
    SystemRole.MANAGER: frozenset(
        {
            IamPermission.VIEW_CALLS,
            IamPermission.APPROVE_WORKFLOWS,
            IamPermission.EXECUTE_TOOLS,
            IamPermission.VIEW_ANALYTICS,
            IamPermission.MANAGE_KNOWLEDGE,
        }
    ),
    SystemRole.AGENT: frozenset(
        {IamPermission.VIEW_CALLS, IamPermission.EXECUTE_TOOLS, IamPermission.MANAGE_KNOWLEDGE}
    ),
    SystemRole.DEVELOPER: frozenset(
        {
            IamPermission.MANAGE_AGENTS,
            IamPermission.MANAGE_API_KEYS,
            IamPermission.EXECUTE_TOOLS,
            IamPermission.VIEW_AUDIT_LOGS,
        }
    ),
    SystemRole.BILLING: frozenset({IamPermission.MANAGE_BILLING, IamPermission.VIEW_ANALYTICS}),
    SystemRole.SECURITY_AUDITOR: frozenset(
        {IamPermission.VIEW_AUDIT_LOGS, IamPermission.MANAGE_SECURITY, IamPermission.VIEW_CALLS}
    ),
    SystemRole.VIEWER: frozenset({IamPermission.VIEW_CALLS, IamPermission.VIEW_ANALYTICS}),
}
