"""IAM subsystem factory."""

from functools import lru_cache

from app.infrastructure.iam.iam_service_impl import IamServiceImpl
from app.infrastructure.repositories.iam.repositories import (
    SqlAlchemyApiKeyRepository,
    SqlAlchemyIamAuditRepository,
    SqlAlchemyMembershipRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemySecurityEventRepository,
    SqlAlchemySecurityPolicyRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyUserRepository,
)
from app.iam.audit.audit_service import IamAuditService
from app.iam.metrics.collector import IamMetricsCollector
from app.iam.services.iam_service import IamService


@lru_cache
def get_iam_metrics_collector() -> IamMetricsCollector:
    return IamMetricsCollector()


def build_iam_service(session) -> IamService:
    audit_repo = SqlAlchemyIamAuditRepository(session)
    impl = IamServiceImpl(
        organizations=SqlAlchemyOrganizationRepository(session),
        users=SqlAlchemyUserRepository(session),
        memberships=SqlAlchemyMembershipRepository(session),
        roles=SqlAlchemyRoleRepository(session),
        api_keys=SqlAlchemyApiKeyRepository(session),
        sessions=SqlAlchemySessionRepository(session),
        policies=SqlAlchemySecurityPolicyRepository(session),
        audit=IamAuditService(audit_repo),
        security_events=SqlAlchemySecurityEventRepository(session),
        metrics=get_iam_metrics_collector(),
    )
    return IamService(impl)
