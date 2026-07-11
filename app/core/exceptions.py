"""Application-level exceptions (mapped to HTTP in API layer)."""


class NotFoundError(Exception):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message)


class ConflictError(Exception):
    """Resource conflict (duplicate slug, etc.)."""

    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(message)


class DatabaseUnavailableError(Exception):
    """Database not configured or unreachable."""

    def __init__(self, message: str = "Database unavailable") -> None:
        super().__init__(message)


class RetrievalValidationError(Exception):
    """Retrieved context failed validation before LLM injection."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class CrossTenantAccessError(RetrievalValidationError):
    """Attempted cross-tenant knowledge access."""


class UnauthorizedAgentAccessError(RetrievalValidationError):
    """Agent not authorized for requested knowledge scope."""


class MemoryAccessError(Exception):
    """Memory access validation failed."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class CrossTenantMemoryError(MemoryAccessError):
    """Attempted cross-tenant memory access."""


class SessionExpiredError(MemoryAccessError):
    """Session is expired or no longer active."""


class SessionNotFoundError(NotFoundError):
    """Conversation session not found."""


class ToolNotFoundError(NotFoundError):
    """Tool not registered or not found for tenant."""


class ToolPermissionDeniedError(Exception):
    """Tool execution denied by tenant policy."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class ToolValidationError(Exception):
    """Tool input or schema validation failed."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class ToolExecutionError(Exception):
    """Tool execution failed at runtime."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class ToolRateLimitError(Exception):
    """Tenant or tool rate limit exceeded."""


class ToolCircuitOpenError(ToolExecutionError):
    """Circuit breaker is open for external provider."""


class CrossTenantToolError(Exception):
    """Attempted cross-tenant tool access."""


class PlannerPolicyViolationError(Exception):
    """Planner output or request violates tenant policy."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class PlannerConfidenceTooLowError(Exception):
    """Planner confidence below threshold."""

    def __init__(self, message: str, *, confidence: float = 0.0) -> None:
        super().__init__(message)
        self.confidence = confidence


class PlannerValidationError(Exception):
    """Planner output failed structural validation."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class CrossTenantPlannerError(Exception):
    """Attempted cross-tenant planner access."""


class PlannerSessionNotFoundError(NotFoundError):
    """Planner session not found."""


class VerifierRejectionError(Exception):
    """Verifier rejected planner decision."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class VerifierPolicyViolationError(Exception):
    """Tenant policy violation detected by verifier."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class VerifierComplianceError(Exception):
    """Compliance framework check failed."""

    def __init__(self, message: str, *, framework: str | None = None) -> None:
        super().__init__(message)
        self.framework = framework


class VerifierValidationError(Exception):
    """Verifier input/output validation failed."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class CrossTenantVerifierError(Exception):
    """Attempted cross-tenant verifier access."""


class WorkflowNotFoundError(NotFoundError):
    """Workflow definition or execution not found."""


class WorkflowExecutionError(Exception):
    """Workflow execution failed."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class WorkflowPolicyViolationError(Exception):
    """Workflow policy violation."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class WorkflowApprovalRequiredError(Exception):
    """Workflow paused pending approval."""

    def __init__(self, message: str, *, approval_id: str | None = None) -> None:
        super().__init__(message)
        self.approval_id = approval_id


class WorkflowValidationError(Exception):
    """Workflow definition or input validation failed."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class CrossTenantWorkflowError(Exception):
    """Attempted cross-tenant workflow access."""


class AuthenticationError(Exception):
    """Authentication failed."""


class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password."""


class TokenExpiredError(AuthenticationError):
    """Token or session expired."""


class MfaRequiredError(AuthenticationError):
    """Multi-factor authentication required."""

    def __init__(self, message: str = "MFA required", *, challenge_id: str | None = None) -> None:
        super().__init__(message)
        self.challenge_id = challenge_id


class AuthorizationError(Exception):
    """Authorization failed."""

    def __init__(self, message: str, *, permission: str | None = None) -> None:
        super().__init__(message)
        self.permission = permission


class InsufficientPermissionsError(AuthorizationError):
    """User lacks required permission."""


class IamUserNotFoundError(NotFoundError):
    """IAM user not found."""


class OrganizationNotFoundError(NotFoundError):
    """Organization not found."""


class ApiKeyNotFoundError(NotFoundError):
    """API key not found."""


class IamSessionNotFoundError(NotFoundError):
    """Auth session not found."""


class CrossOrganizationAccessError(Exception):
    """Attempted cross-organization access."""


class IamValidationError(Exception):
    """IAM input validation failed."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []


class SecurityPolicyViolationError(Exception):
    """Organization security policy violation."""

    def __init__(self, message: str, *, violations: list[str] | None = None) -> None:
        super().__init__(message)
        self.violations = violations or []
