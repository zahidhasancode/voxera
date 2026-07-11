"""SQLAlchemy ORM models — import all for Alembic metadata registration."""

from app.database.models.agent import AgentModel
from app.database.models.audit import AuditLogModel
from app.database.models.configuration import AgentConfigurationModel
from app.database.models.knowledge import KnowledgeBaseModel
from app.database.models.knowledge_source import KnowledgeChunkModel, KnowledgeSourceModel
from app.database.models.knowledge_job import KnowledgeIngestionJobModel
from app.database.models.memory import (
    ConversationModel,
    ConversationSummaryModel,
    ConversationTurnModel,
    ToolExecutionModel,
    WorkingMemoryModel,
)
from app.database.models.tenant import TenantModel
from app.database.models.tool import ToolModel
from app.database.models.tool_framework import (
    TenantToolConfigModel,
    ToolAuditModel,
    ToolFrameworkExecutionModel,
    ToolPermissionModel,
)

from app.database.models.planner import (
    PlannerDecisionModel,
    PlannerHistoryModel,
    PlannerMetricsModel,
    PlannerSessionModel,
)

from app.database.models.verifier import (
    ComplianceCheckModel,
    PolicyViolationModel,
    RiskAssessmentModel,
    VerifierAuditModel,
    VerifierDecisionModel,
)

from app.database.models.workflow import (
    BusinessPolicyModel,
    RoutingRuleModel,
    WorkflowApprovalModel,
    WorkflowAuditModel,
    WorkflowEscalationModel,
    WorkflowExecutionModel,
    WorkflowModel,
    WorkflowRuleModel,
)

from app.database.models.iam import (
    ComplianceSettingsModel,
    IamApiKeyModel,
    IamAuditLogModel,
    IamRoleModel,
    IamSecurityEventModel,
    IamSecurityPolicyModel,
    IamSessionModel,
    IamUserModel,
    MfaFactorModel,
    OAuthIdentityModel,
    OrganizationMembershipModel,
    OrganizationModel,
    SsoProviderModel,
)

from app.database.models.integration import (
    IntegrationAuditLogModel,
    IntegrationConnectionModel,
    IntegrationCredentialModel,
    IntegrationFieldMappingModel,
    IntegrationSyncCursorModel,
    IntegrationSyncJobModel,
    IntegrationWebhookDlqModel,
    IntegrationWebhookEventModel,
)

__all__ = [
    "TenantModel",
    "AgentModel",
    "AgentConfigurationModel",
    "KnowledgeBaseModel",
    "KnowledgeSourceModel",
    "KnowledgeChunkModel",
    "KnowledgeIngestionJobModel",
    "ToolModel",
    "AuditLogModel",
    "ConversationModel",
    "ConversationTurnModel",
    "ConversationSummaryModel",
    "WorkingMemoryModel",
    "ToolExecutionModel",
    "ToolPermissionModel",
    "TenantToolConfigModel",
    "ToolFrameworkExecutionModel",
    "ToolAuditModel",
    "PlannerSessionModel",
    "PlannerDecisionModel",
    "PlannerHistoryModel",
    "PlannerMetricsModel",
    "VerifierDecisionModel",
    "RiskAssessmentModel",
    "PolicyViolationModel",
    "ComplianceCheckModel",
    "VerifierAuditModel",
    "WorkflowModel",
    "WorkflowExecutionModel",
    "WorkflowRuleModel",
    "WorkflowApprovalModel",
    "WorkflowEscalationModel",
    "BusinessPolicyModel",
    "RoutingRuleModel",
    "WorkflowAuditModel",
    "OrganizationModel",
    "IamUserModel",
    "OrganizationMembershipModel",
    "IamRoleModel",
    "IamApiKeyModel",
    "IamSessionModel",
    "IamSecurityPolicyModel",
    "IamSecurityEventModel",
    "IamAuditLogModel",
    "OAuthIdentityModel",
    "SsoProviderModel",
    "MfaFactorModel",
    "ComplianceSettingsModel",
    "IntegrationConnectionModel",
    "IntegrationCredentialModel",
    "IntegrationFieldMappingModel",
    "IntegrationSyncJobModel",
    "IntegrationSyncCursorModel",
    "IntegrationWebhookEventModel",
    "IntegrationWebhookDlqModel",
    "IntegrationAuditLogModel",
]
