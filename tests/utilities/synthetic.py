"""Synthetic test data generators."""

from __future__ import annotations

from uuid import UUID, uuid4

from dataclasses import dataclass


@dataclass
class SyntheticOrganization:
    id: UUID
    name: str
    slug: str
    tenant_id: UUID


@dataclass
class SyntheticCustomer:
    id: UUID
    name: str
    email: str
    phone: str


def synthetic_organization(name: str = "Acme QA Corp") -> SyntheticOrganization:
    tid = uuid4()
    return SyntheticOrganization(
        id=uuid4(),
        name=name,
        slug=name.lower().replace(" ", "-"),
        tenant_id=tid,
    )


def synthetic_customer(index: int = 1) -> SyntheticCustomer:
    return SyntheticCustomer(
        id=uuid4(),
        name=f"QA Customer {index}",
        email=f"customer{index}@qa.voxera.test",
        phone=f"+1555000{index:04d}",
    )


def synthetic_conversation_turns(count: int = 5) -> list[dict[str, str]]:
    roles = ["user", "agent"]
    turns = []
    for i in range(count):
        role = roles[i % 2]
        if role == "user":
            text = f"Customer message {i + 1}"
        else:
            text = f"Agent response {i + 1}"
        turns.append({"role": role, "text": text})
    return turns
