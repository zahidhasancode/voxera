"""IAM access validation."""

from uuid import UUID

from app.core.exceptions import CrossOrganizationAccessError


class IamAccessValidator:
    def validate_org_scope(self, *, actor_org_id: UUID, resource_org_id: UUID) -> None:
        if actor_org_id != resource_org_id:
            raise CrossOrganizationAccessError(
                f"Cross-organization access denied: {actor_org_id} != {resource_org_id}"
            )
