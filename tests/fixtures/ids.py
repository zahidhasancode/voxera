"""Stable UUID fixtures for multi-tenant tests."""

from __future__ import annotations

from uuid import UUID

import pytest

TENANT_A = UUID("11111111-1111-4111-8111-111111111111")
TENANT_B = UUID("22222222-2222-4222-8222-222222222222")
ORG_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
USER_A = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
AGENT_A = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")


@pytest.fixture
def tenant_id():
    return TENANT_A


@pytest.fixture
def tenant_id_b():
    return TENANT_B


@pytest.fixture
def organization_id():
    return ORG_A


@pytest.fixture
def user_id():
    return USER_A


@pytest.fixture
def agent_id():
    return AGENT_A
