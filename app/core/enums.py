"""Shared domain enumerations for enterprise multi-tenant resources."""

from enum import StrEnum


class TenantStatus(StrEnum):
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class SubscriptionPlan(StrEnum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class AgentStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class KnowledgeBaseStatus(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class KnowledgeSourceType(StrEnum):
    """Supported and future-ready knowledge source types."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    CSV_FAQ = "csv_faq"
    WEBSITE = "website"
    # Future integrations
    CONFLUENCE = "confluence"
    NOTION = "notion"
    GOOGLE_DRIVE = "google_drive"
    SHAREPOINT = "sharepoint"


class KnowledgeSourceStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    REPROCESSING = "reprocessing"


class KnowledgeEmbeddingStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"


class KnowledgeProcessingStage(StrEnum):
    """Pipeline stages for logging and progress tracking."""

    UPLOAD = "upload"
    PARSE = "parse"
    CLEAN = "clean"
    CHUNK = "chunk"
    METADATA = "metadata"
    EMBED = "embed"
    VECTOR_STORE = "vector_store"
    COMPLETE = "complete"
    FAILED = "failed"


class KnowledgeIngestionJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class ChunkStrategyType(StrEnum):
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"
    MARKDOWN = "markdown"
    TOKEN = "token"


class EmbeddingProviderType(StrEnum):
    """Registry of supported embedding provider identifiers (not implementations)."""

    OPENAI = "openai"
    VOYAGEAI = "voyageai"
    BGE = "bge"
    INSTRUCTOR = "instructor"
    NOMIC = "nomic"
    AZURE_OPENAI = "azure_openai"


class VectorStoreType(StrEnum):
    """Registry of supported vector store identifiers (not implementations)."""

    QDRANT = "qdrant"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    PGVECTOR = "pgvector"
    MILVUS = "milvus"


class STTProviderType(StrEnum):
    DEEPGRAM = "deepgram"
    GOOGLE_SPEECH = "google_speech"
    AZURE_SPEECH = "azure_speech"
    ASSEMBLYAI = "assemblyai"
    OPENAI_REALTIME = "openai_realtime"
    AMAZON_TRANSCRIBE = "amazon_transcribe"


class LLMProviderType(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    AZURE_OPENAI = "azure_openai"
    GROQ = "groq"


class TTSProviderType(StrEnum):
    ELEVENLABS = "elevenlabs"
    AZURE_TTS = "azure_tts"
    GOOGLE_TTS = "google_tts"
    CARTESIA = "cartesia"
    OPENAI_AUDIO = "openai_audio"
    AMAZON_POLLY = "amazon_polly"


class CallSessionStateType(StrEnum):
    """Extended call lifecycle states for telephony sessions."""

    INCOMING = "incoming"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    PAUSED = "paused"
    INTERRUPTED = "interrupted"
    TRANSFERRED = "transferred"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    ENDED = "ended"


class ToolStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


class ToolHandlerType(StrEnum):
    BUILTIN = "builtin"
    HTTP = "http"
    MCP = "mcp"


class AuditActorType(StrEnum):
    USER = "user"
    SYSTEM = "system"
    API_KEY = "api_key"
    SERVICE = "service"


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    EXPIRED = "expired"


class MemoryRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class SessionState(StrEnum):
    CALL_STARTED = "call_started"
    IDENTITY_PENDING = "identity_pending"
    IDENTITY_VERIFIED = "identity_verified"
    RETRIEVAL_RUNNING = "retrieval_running"
    TOOL_EXECUTION = "tool_execution"
    WAITING_CONFIRMATION = "waiting_confirmation"
    ESCALATED = "escalated"
    CALL_COMPLETED = "call_completed"


class ToolExecutionStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class WorkingMemoryKey(StrEnum):
    CUSTOMER_NAME = "customer_name"
    EMAIL = "email"
    PHONE = "phone"
    APPOINTMENT_ID = "appointment_id"
    ORDER_NUMBER = "order_number"
    SELECTED_PRODUCT = "selected_product"
    CURRENT_INTENT = "current_intent"
    VERIFICATION_STATUS = "verification_status"
    CUSTOM = "custom"


class ToolPermissionEffect(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"


class ToolBuiltinSlug(StrEnum):
    """Built-in tool identifiers — plugin registry keys."""

    APPOINTMENT = "appointment"
    CALENDAR = "calendar"
    EMAIL = "email"
    SMS = "sms"
    CRM_LOOKUP = "crm_lookup"
    CRM_UPDATE = "crm_update"
    ORDER_LOOKUP = "order_lookup"
    TICKET_CREATION = "ticket_creation"
    FAQ_SEARCH = "faq_search"
    HUMAN_TRANSFER = "human_transfer"
    IDENTITY_VERIFICATION = "identity_verification"
    WEBHOOK = "webhook"


class ToolFrameworkExecutionStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PERMISSION_DENIED = "permission_denied"
    VALIDATION_FAILED = "validation_failed"
    CIRCUIT_OPEN = "circuit_open"


class ToolAuditStatus(StrEnum):
    REQUESTED = "requested"
    VALIDATED = "validated"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    DENIED = "denied"


class CircuitBreakerState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class PlannerAction(StrEnum):
    RESPOND = "respond"
    RETRIEVE = "retrieve"
    CALL_TOOL = "call_tool"
    ASK_CLARIFICATION = "ask_clarification"
    ESCALATE = "escalate"
    TRANSFER_HUMAN = "transfer_human"
    END_CONVERSATION = "end_conversation"


class PlannerIntent(StrEnum):
    ORDER_STATUS = "order_status"
    APPOINTMENT = "appointment"
    REFUND = "refund"
    CANCEL_SUBSCRIPTION = "cancel_subscription"
    TECHNICAL_ISSUE = "technical_issue"
    COMPLAINT = "complaint"
    GENERAL_QUESTION = "general_question"
    IDENTITY_VERIFICATION = "identity_verification"
    EMERGENCY = "emergency"
    GREETING = "greeting"
    UNKNOWN = "unknown"


class PlannerRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PlannerDecisionStatus(StrEnum):
    COMPLETED = "completed"
    NEEDS_RETRIEVAL = "needs_retrieval"
    NEEDS_TOOL = "needs_tool"
    NEEDS_CLARIFICATION = "needs_clarification"
    ESCALATED = "escalated"
    FAILED = "failed"
    POLICY_BLOCKED = "policy_blocked"


class PlannerSessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    FAILED = "failed"


class SupportedLanguage(StrEnum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    AR = "ar"
    BN = "bn"


class VerifierOutcome(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    REQUIRES_CONFIRMATION = "requires_confirmation"


class VerifierRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceFramework(StrEnum):
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    ISO27001 = "iso27001"


class IdentityVerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


class VerifierAuditStatus(StrEnum):
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    POLICY_VIOLATION = "policy_violation"
    COMPLIANCE_FAILURE = "compliance_failure"


class WorkflowState(StrEnum):
    STARTED = "started"
    WAITING_APPROVAL = "waiting_approval"
    WAITING_IDENTITY = "waiting_identity"
    WAITING_CUSTOMER = "waiting_customer"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
    TIMEOUT = "timeout"
    REJECTED = "rejected"


class WorkflowEventType(StrEnum):
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_PAUSED = "workflow_paused"
    WORKFLOW_RESUMED = "workflow_resumed"
    WORKFLOW_APPROVED = "workflow_approved"
    WORKFLOW_REJECTED = "workflow_rejected"
    WORKFLOW_ESCALATED = "workflow_escalated"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_TIMEOUT = "workflow_timeout"
    RULE_MATCHED = "rule_matched"
    POLICY_EVALUATED = "policy_evaluated"
    ROUTING_DECIDED = "routing_decided"


class WorkflowApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SKIPPED = "skipped"


class WorkflowApprovalMode(StrEnum):
    AUTO = "auto"
    MANAGER = "manager"
    DEPARTMENT = "department"
    TWO_STEP = "two_step"
    TIME_LIMITED = "time_limited"


class EscalationTarget(StrEnum):
    HUMAN_AGENT = "human_agent"
    SUPERVISOR = "supervisor"
    DEPARTMENT = "department"
    EMERGENCY_QUEUE = "emergency_queue"
    SMS = "sms"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"


class RoutingStrategy(StrEnum):
    DEPARTMENT = "department"
    SKILL = "skill"
    LANGUAGE = "language"
    PRIORITY = "priority"
    VIP = "vip"
    EMERGENCY = "emergency"
    ROUND_ROBIN = "round_robin"


class RuleOperator(StrEnum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"


class RuleActionType(StrEnum):
    REQUIRE_APPROVAL = "require_approval"
    REJECT = "reject"
    ESCALATE = "escalate"
    ROUTE = "route"
    EXECUTE = "execute"
    NOTIFY = "notify"
    PAUSE = "pause"
    COMPLETE = "complete"
    BYPASS_AUTH = "bypass_auth"


class WorkflowExecutionStatus(StrEnum):
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
    TIMEOUT = "timeout"
    REJECTED = "rejected"


# --- Enterprise IAM ---


class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class IamUserStatus(StrEnum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class IamMembershipStatus(StrEnum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"


class SystemRole(StrEnum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    AGENT = "agent"
    DEVELOPER = "developer"
    BILLING = "billing"
    SECURITY_AUDITOR = "security_auditor"
    VIEWER = "viewer"


class IamPermission(StrEnum):
    VIEW_CALLS = "view_calls"
    DELETE_CALLS = "delete_calls"
    MANAGE_AGENTS = "manage_agents"
    MANAGE_KNOWLEDGE = "manage_knowledge"
    MANAGE_BILLING = "manage_billing"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXECUTE_TOOLS = "execute_tools"
    APPROVE_WORKFLOWS = "approve_workflows"
    MANAGE_USERS = "manage_users"
    MANAGE_API_KEYS = "manage_api_keys"
    MANAGE_ROLES = "manage_roles"
    MANAGE_SECURITY = "manage_security"
    MANAGE_ORGANIZATION = "manage_organization"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_INTEGRATIONS = "manage_integrations"
    VIEW_INTEGRATIONS = "view_integrations"


class ApiKeyStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ApiKeyEnvironment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class IamSessionStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AuthMethod(StrEnum):
    PASSWORD = "password"
    MAGIC_LINK = "magic_link"
    OAUTH = "oauth"
    SSO = "sso"
    API_KEY = "api_key"


class OAuthProvider(StrEnum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    OKTA = "okta"
    AUTH0 = "auth0"


class SsoProviderType(StrEnum):
    SAML = "saml"
    OIDC = "oidc"
    OKTA = "okta"
    ENTRA_ID = "entra_id"
    GOOGLE_WORKSPACE = "google_workspace"
    ONELOGIN = "onelogin"
    PING = "ping"
    AUTH0 = "auth0"


class MfaFactorType(StrEnum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODES = "backup_codes"
    WEBAUTHN = "webauthn"


class SecurityEventType(StrEnum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    MFA_FAILURE = "mfa_failure"
    PERMISSION_DENIED = "permission_denied"
    POLICY_VIOLATION = "policy_violation"
    API_ABUSE = "api_abuse"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    ROLE_UPDATED = "role_updated"
    SESSION_REVOKED = "session_revoked"


class SecurityEventSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"



# ---------------------------------------------------------------------------
# Enterprise Integration Platform
# ---------------------------------------------------------------------------


class IntegrationCategory(StrEnum):
    CRM = "crm"
    HELPDESK = "helpdesk"
    ECOMMERCE = "ecommerce"
    CALENDAR = "calendar"
    EMAIL = "email"
    IDENTITY = "identity"
    COMMUNICATION = "communication"
    PAYMENT = "payment"
    KNOWLEDGE = "knowledge"
    PHONE = "phone"
    CUSTOM = "custom"


class IntegrationConnectionStatus(StrEnum):
    PENDING = "pending"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    EXPIRED = "expired"
    REVOKED = "revoked"


class IntegrationHealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class IntegrationSyncMode(StrEnum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    INCREMENTAL = "incremental"
    FULL = "full"


class IntegrationSyncJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


class IntegrationEntityType(StrEnum):
    CUSTOMER = "customer"
    PRODUCT = "product"
    ORDER = "order"
    APPOINTMENT = "appointment"
    TICKET = "ticket"
    EMPLOYEE = "employee"
    KNOWLEDGE = "knowledge"
    CALENDAR_EVENT = "calendar_event"
    EMAIL = "email"
    CONTACT = "contact"
    INVOICE = "invoice"
    SUBSCRIPTION = "subscription"


class IntegrationCredentialType(StrEnum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    WEBHOOK_SECRET = "webhook_secret"
    BASIC_AUTH = "basic_auth"
    CUSTOM = "custom"


class IntegrationWebhookEventStatus(StrEnum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DUPLICATE = "duplicate"
    DEAD_LETTER = "dead_letter"


class IntegrationAuthType(StrEnum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    WEBHOOK_ONLY = "webhook_only"
    SIP = "sip"
    CUSTOM = "custom"


class IntegrationProviderSlug(StrEnum):
    """Registry of supported integration provider identifiers."""

    # CRM
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"
    ZOHO_CRM = "zoho_crm"
    MICROSOFT_DYNAMICS = "microsoft_dynamics"
    PIPEDRIVE = "pipedrive"
    FRESHSALES = "freshsales"
    CUSTOM_CRM = "custom_crm"
    # Helpdesk
    ZENDESK = "zendesk"
    FRESHDESK = "freshdesk"
    INTERCOM = "intercom"
    SERVICENOW = "servicenow"
    HELP_SCOUT = "help_scout"
    ZOHO_DESK = "zoho_desk"
    # Ecommerce
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    MAGENTO = "magento"
    BIGCOMMERCE = "bigcommerce"
    PRESTASHOP = "prestashop"
    # Calendar
    GOOGLE_CALENDAR = "google_calendar"
    MICROSOFT_OUTLOOK = "microsoft_outlook"
    CALENDLY = "calendly"
    APPLE_CALENDAR = "apple_calendar"
    # Email
    GMAIL = "gmail"
    MICROSOFT_365 = "microsoft_365"
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    AMAZON_SES = "amazon_ses"
    # Identity
    MICROSOFT_ENTRA = "microsoft_entra"
    OKTA = "okta"
    GOOGLE_WORKSPACE = "google_workspace"
    AZURE_AD = "azure_ad"
    # Communication
    SLACK = "slack"
    MICROSOFT_TEAMS = "microsoft_teams"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    # Payment
    STRIPE = "stripe"
    PAYPAL = "paypal"
    ADYEN = "adyen"
    # Knowledge
    NOTION = "notion"
    CONFLUENCE = "confluence"
    GOOGLE_DRIVE = "google_drive"
    SHAREPOINT = "sharepoint"
    DROPBOX = "dropbox"
    ONEDRIVE = "onedrive"
    BOX = "box"
    # Phone
    TWILIO = "twilio"
    SIP = "sip"
    BYOC = "byoc"
