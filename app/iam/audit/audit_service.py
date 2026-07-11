"""Immutable IAM audit service."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.iam.schemas import IamAuditRead


class IamAuditService:
    def __init__(self, repository) -> None:
        self._repository = repository

    async def log(
        self,
        *,
        organization_id: UUID,
        action: str,
        resource_type: str,
        actor_user_id: UUID | None = None,
        actor_type: str = "user",
        resource_id: str | None = None,
        ip_address: str | None = None,
        payload: dict | None = None,
    ) -> IamAuditRead:
        entry = IamAuditRead(
            id=uuid4(),
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_type=actor_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            payload=payload,
            occurred_at=datetime.now(timezone.utc),
        )
        return await self._repository.append(entry)
