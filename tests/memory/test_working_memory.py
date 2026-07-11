"""Unit tests for working memory and session lifecycle."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.enums import ConversationStatus, SessionState
from app.memory.schemas import SessionRead, WorkingMemoryRead
from app.memory.validators.access_validator import MemoryAccessValidator
from app.core.exceptions import CrossTenantMemoryError, SessionExpiredError


@pytest.fixture
def tenant_id():
    return uuid4()


def _session(tenant_id, agent_id, conversation_id, *, status=ConversationStatus.ACTIVE):
    now = datetime.now(timezone.utc)
    return SessionRead(
        id=conversation_id,
        tenant_id=tenant_id,
        agent_id=agent_id,
        status=status,
        current_state=SessionState.CALL_STARTED,
        language="en",
        turn_count=0,
        started_at=now,
        ended_at=None,
        expires_at=now + timedelta(hours=24),
        metadata=None,
        created_at=now,
        updated_at=now,
    )


def test_validator_redacts_sensitive_fields():
    validator = MemoryAccessValidator()
    result = validator.redact_sensitive(
        {"customer_name": "Alice", "email": "a@b.com"},
        {"email"},
    )
    assert result["customer_name"] == "Alice"
    assert result["email"] == "[REDACTED]"


def test_validator_rejects_cross_tenant(tenant_id):
    validator = MemoryAccessValidator()
    other = uuid4()
    session = _session(other, uuid4(), uuid4())
    with pytest.raises(CrossTenantMemoryError):
        validator.validate_session_access(
            session, tenant_id=tenant_id, agent_id=session.agent_id, conversation_id=session.id
        )


def test_validator_rejects_expired_session(tenant_id):
    validator = MemoryAccessValidator()
    agent_id = uuid4()
    conversation_id = uuid4()
    session = _session(tenant_id, agent_id, conversation_id, status=ConversationStatus.EXPIRED)
    with pytest.raises(SessionExpiredError):
        validator.validate_session_access(
            session, tenant_id=tenant_id, agent_id=agent_id, conversation_id=conversation_id
        )
