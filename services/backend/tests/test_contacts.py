from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.auth.models import OrganizationMember, User
from mini_crm.modules.contacts.dto.schemas import ContactCreate
from mini_crm.modules.contacts.repositories.sqlalchemy import SQLAlchemyContactRepository
from mini_crm.modules.organizations.models import Organization
from mini_crm.shared.enums import UserRole

HEADERS = {"Authorization": "Bearer test", "X-Organization-Id": "1"}


async def seed_user_and_org(session: AsyncSession) -> None:
    now = datetime.now(tz=UTC)
    organization = Organization(id=1, name="Acme Inc", created_at=now)
    user = User(
        id=1,
        email="owner@example.com",
        hashed_password="hashed",
        name="Owner",
        created_at=now,
    )
    session.add_all([organization, user])
    await session.commit()


async def seed_organization_member(
    session: AsyncSession, user_id: int, organization_id: int, role: UserRole = UserRole.OWNER
) -> OrganizationMember:
    member = OrganizationMember(
        user_id=user_id,
        organization_id=organization_id,
        role=role,
    )
    session.add(member)
    await session.commit()
    await session.refresh(member)
    return member


@pytest.mark.asyncio
async def test_sqlalchemy_contact_repository(db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    repository = SQLAlchemyContactRepository(session=db_session)

    payload = ContactCreate(name="John", email="john@example.com", phone="+111111")
    created = await repository.create(organization_id=1, owner_id=1, payload=payload)

    assert created.id == 1
    assert created.owner_id == 1

    items, total = await repository.list(organization_id=1, page=1, page_size=10)
    assert total == 1
    assert items[0].name == "John"


@pytest.mark.asyncio
async def test_contact_crud_flow(api_client: AsyncClient, db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)

    create_payload = {"name": "John", "email": "john@example.com", "phone": "+111111"}
    create_response = await api_client.post(
        "/api/v1/contacts",
        json=create_payload,
        headers=HEADERS,
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["name"] == "John"

    list_response = await api_client.get("/api/v1/contacts", headers=HEADERS)
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["meta"]["total"] == 1
    assert data["items"][0]["name"] == "John"
