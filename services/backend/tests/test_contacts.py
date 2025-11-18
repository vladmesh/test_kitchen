from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.security import create_access_token
from mini_crm.modules.auth.models import OrganizationMember, User
from mini_crm.modules.contacts.dto.schemas import ContactCreate
from mini_crm.modules.contacts.models import Contact
from mini_crm.modules.contacts.repositories.sqlalchemy import SQLAlchemyContactRepository
from mini_crm.modules.deals.models import Deal
from mini_crm.modules.organizations.models import Organization
from mini_crm.shared.enums import DealStage, DealStatus, UserRole

HEADERS = {
    "Authorization": f"Bearer {create_access_token(1)}",
    "X-Organization-Id": "1",
}


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


async def seed_contact(session: AsyncSession, organization_id: int, owner_id: int) -> Contact:
    contact = Contact(
        id=1,
        organization_id=organization_id,
        owner_id=owner_id,
        name="John Doe",
        email="john@example.com",
        phone="+111111",
        created_at=datetime.now(tz=UTC),
    )
    session.add(contact)
    await session.commit()
    return contact


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


@pytest.mark.asyncio
async def test_delete_contact_success(api_client: AsyncClient, db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    delete_response = await api_client.delete("/api/v1/contacts/1", headers=HEADERS)
    assert delete_response.status_code == 204

    # Verify contact is deleted
    list_response = await api_client.get("/api/v1/contacts", headers=HEADERS)
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_contacts_search_filter(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)

    await api_client.post(
        "/api/v1/contacts",
        json={"name": "Alice Smith", "email": "alice@example.com", "phone": "+111111"},
        headers=HEADERS,
    )
    await api_client.post(
        "/api/v1/contacts",
        json={"name": "Bob Johnson", "email": "bob@example.com", "phone": "+222222"},
        headers=HEADERS,
    )

    list_response = await api_client.get(
        "/api/v1/contacts",
        params={"search": "alice"},
        headers=HEADERS,
    )
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["meta"]["total"] == 1
    assert data["items"][0]["name"] == "Alice Smith"


@pytest.mark.asyncio
async def test_delete_contact_with_deals_fails(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create a deal for the contact
    deal = Deal(
        id=1,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        title="Test Deal",
        amount=Decimal("1000.00"),
        currency="USD",
        status=DealStatus.NEW,
        stage=DealStage.QUALIFICATION,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    db_session.add(deal)
    await db_session.commit()

    delete_response = await api_client.delete("/api/v1/contacts/1", headers=HEADERS)
    assert delete_response.status_code == 409
    assert (
        "Cannot delete contact" in delete_response.json()["detail"]
        and "existing deals" in delete_response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_delete_contact_member_permission_check(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    from fastapi import Depends

    from mini_crm.app.main import app
    from mini_crm.core.dependencies import get_request_context, get_request_user
    from mini_crm.modules.common.context import OrganizationContext, RequestContext, RequestUser
    from mini_crm.modules.organizations.repositories.sqlalchemy import (
        SQLAlchemyOrganizationRepository,
    )

    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1, role=UserRole.OWNER)

    # Create second user
    user2 = User(
        id=2,
        email="member@example.com",
        hashed_password="hashed",
        name="Member",
        created_at=datetime.now(tz=UTC),
    )
    db_session.add(user2)
    await db_session.commit()
    await seed_organization_member(db_session, user_id=2, organization_id=1, role=UserRole.MEMBER)

    # Create contact owned by user 1
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Override get_request_user to return user 2
    async def override_get_request_user() -> RequestUser:
        return RequestUser(id=2, email="member@example.com")

    from fastapi import Header

    from mini_crm.core.dependencies import get_db_session

    async def override_get_request_context(
        user: RequestUser = Depends(override_get_request_user),
        organization_id: int | None = Header(default=None, alias="X-Organization-Id"),
        session: AsyncSession = Depends(get_db_session),
    ) -> RequestContext:
        if organization_id is None:
            organization_id = 1
        repository = SQLAlchemyOrganizationRepository(session)
        membership = await repository.get_membership(user.id, organization_id)
        role = (
            membership.role if isinstance(membership.role, UserRole) else UserRole(membership.role)
        )
        org_context = OrganizationContext(organization_id=organization_id, role=role)
        return RequestContext(user=user, organization=org_context)

    app.dependency_overrides[get_request_user] = override_get_request_user
    app.dependency_overrides[get_request_context] = override_get_request_context

    try:
        # Try to delete contact owned by user 1 as user 2 (member) - should fail
        member_headers = {"Authorization": "Bearer test", "X-Organization-Id": "1"}
        delete_response = await api_client.delete("/api/v1/contacts/1", headers=member_headers)
        assert delete_response.status_code == 403
        assert "You can only delete your own contacts" in delete_response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_request_user, None)
        app.dependency_overrides.pop(get_request_context, None)


@pytest.mark.asyncio
async def test_delete_contact_member_can_delete_own(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    from fastapi import Depends

    from mini_crm.app.main import app
    from mini_crm.core.dependencies import get_request_context, get_request_user
    from mini_crm.modules.common.context import OrganizationContext, RequestContext, RequestUser
    from mini_crm.modules.organizations.repositories.sqlalchemy import (
        SQLAlchemyOrganizationRepository,
    )

    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1, role=UserRole.OWNER)

    # Create second user
    user2 = User(
        id=2,
        email="member@example.com",
        hashed_password="hashed",
        name="Member",
        created_at=datetime.now(tz=UTC),
    )
    db_session.add(user2)
    await db_session.commit()
    await seed_organization_member(db_session, user_id=2, organization_id=1, role=UserRole.MEMBER)

    # Create contact owned by user 2
    contact = Contact(
        id=1,
        organization_id=1,
        owner_id=2,
        name="Member Contact",
        email="member@example.com",
        phone="+222222",
        created_at=datetime.now(tz=UTC),
    )
    db_session.add(contact)
    await db_session.commit()

    # Override get_request_user to return user 2
    async def override_get_request_user() -> RequestUser:
        return RequestUser(id=2, email="member@example.com")

    from fastapi import Header

    from mini_crm.core.dependencies import get_db_session

    async def override_get_request_context(
        user: RequestUser = Depends(override_get_request_user),
        organization_id: int | None = Header(default=None, alias="X-Organization-Id"),
        session: AsyncSession = Depends(get_db_session),
    ) -> RequestContext:
        if organization_id is None:
            organization_id = 1
        repository = SQLAlchemyOrganizationRepository(session)
        membership = await repository.get_membership(user.id, organization_id)
        role = (
            membership.role if isinstance(membership.role, UserRole) else UserRole(membership.role)
        )
        org_context = OrganizationContext(organization_id=organization_id, role=role)
        return RequestContext(user=user, organization=org_context)

    app.dependency_overrides[get_request_user] = override_get_request_user
    app.dependency_overrides[get_request_context] = override_get_request_context

    try:
        # User 2 (member) can delete their own contact
        member_headers = {"Authorization": "Bearer test", "X-Organization-Id": "1"}
        delete_response = await api_client.delete("/api/v1/contacts/1", headers=member_headers)
        assert delete_response.status_code == 204
    finally:
        app.dependency_overrides.pop(get_request_user, None)
        app.dependency_overrides.pop(get_request_context, None)


@pytest.mark.asyncio
async def test_list_contacts_owner_filter_allowed_roles(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1, role=UserRole.MANAGER)

    # Contact owned by current user (id=1)
    await api_client.post(
        "/api/v1/contacts",
        json={"name": "Owner Contact", "email": "owner@example.com", "phone": "+333333"},
        headers=HEADERS,
    )

    # Second user and contact owned by them
    user2 = User(
        id=2,
        email="manager@example.com",
        hashed_password="hashed",
        name="Manager",
        created_at=datetime.now(tz=UTC),
    )
    db_session.add(user2)
    await db_session.commit()
    await seed_organization_member(db_session, user_id=2, organization_id=1, role=UserRole.MEMBER)

    contact = Contact(
        id=2,
        organization_id=1,
        owner_id=2,
        name="Manager Contact",
        email="manager@example.com",
        phone="+444444",
        created_at=datetime.now(tz=UTC),
    )
    db_session.add(contact)
    await db_session.commit()

    response = await api_client.get(
        "/api/v1/contacts",
        params={"owner_id": 2},
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1
    assert all(item["owner_id"] == 2 for item in data["items"])


@pytest.mark.asyncio
async def test_list_contacts_owner_filter_forbidden_for_member(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1, role=UserRole.MEMBER)

    response = await api_client.get(
        "/api/v1/contacts",
        params={"owner_id": 1},
        headers=HEADERS,
    )
    assert response.status_code == 403
    assert "Filtering by owner_id is not allowed for member role" in response.json()["detail"]
