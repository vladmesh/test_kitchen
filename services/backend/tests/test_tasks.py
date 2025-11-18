from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.security import create_access_token
from mini_crm.modules.auth.models import OrganizationMember, User
from mini_crm.modules.contacts.models import Contact
from mini_crm.modules.deals.models import Deal
from mini_crm.modules.organizations.models import Organization
from mini_crm.modules.tasks.models import Task
from mini_crm.shared.enums import ActivityType, DealStage, DealStatus, UserRole

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
        phone="+123456789",
        created_at=datetime.now(tz=UTC),
    )
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return contact


async def seed_deal(
    session: AsyncSession, organization_id: int, contact_id: int, owner_id: int
) -> Deal:
    deal = Deal(
        id=1,
        organization_id=organization_id,
        contact_id=contact_id,
        owner_id=owner_id,
        title="Test Deal",
        amount=5000.00,
        currency="USD",
        status=DealStatus.NEW,
        stage=DealStage.QUALIFICATION,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    session.add(deal)
    await session.commit()
    await session.refresh(deal)
    return deal


@pytest.mark.asyncio
async def test_create_task_creates_activity(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    from mini_crm.app.main import app
    from mini_crm.modules.activities.repositories.repository import InMemoryActivityRepository
    from mini_crm.modules.tasks.api.router import get_activity_repository

    # Use shared activity repository instance
    shared_activity_repo = InMemoryActivityRepository()
    app.dependency_overrides[get_activity_repository] = lambda: shared_activity_repo

    try:
        await seed_user_and_org(db_session)
        await seed_organization_member(db_session, user_id=1, organization_id=1)
        await seed_contact(db_session, organization_id=1, owner_id=1)
        deal = await seed_deal(db_session, organization_id=1, contact_id=1, owner_id=1)

        # Create task - should create activity
        create_payload = {
            "deal_id": deal.id,
            "title": "Call client",
            "description": "Discuss proposal details",
            "due_date": "2025-12-31T00:00:00Z",
        }
        create_response = await api_client.post(
            "/api/v1/tasks",
            json=create_payload,
            headers=HEADERS,
        )
        assert create_response.status_code == 201
        task_data = create_response.json()
        assert task_data["title"] == "Call client"

        # Check activities using the same repository instance
        activities = await shared_activity_repo.list(organization_id=1, deal_id=deal.id)
        assert len(activities) == 1
        assert activities[0].type.value == ActivityType.TASK_CREATED.value
        assert activities[0].payload is not None
        assert activities[0].payload["task_id"] == task_data["id"]
        assert activities[0].payload["task_title"] == "Call client"
    finally:
        app.dependency_overrides.pop(get_activity_repository, None)


@pytest.mark.asyncio
async def test_create_task_with_past_due_date_fails(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)
    deal = await seed_deal(db_session, organization_id=1, contact_id=1, owner_id=1)

    payload = {
        "deal_id": deal.id,
        "title": "Past due task",
        "description": "Should fail",
        "due_date": (datetime.now(tz=UTC) - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
    }

    response = await api_client.post("/api/v1/tasks", json=payload, headers=HEADERS)
    assert response.status_code == 400
    assert response.json()["detail"] == "due_date cannot be in the past"


@pytest.mark.asyncio
async def test_create_task_with_today_due_date_succeeds(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)
    deal = await seed_deal(db_session, organization_id=1, contact_id=1, owner_id=1)

    today = datetime.now(tz=UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    payload = {
        "deal_id": deal.id,
        "title": "Today due task",
        "description": "Should pass",
        "due_date": today.isoformat().replace("+00:00", "Z"),
    }

    response = await api_client.post("/api/v1/tasks", json=payload, headers=HEADERS)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Today due task"


@pytest.mark.asyncio
async def test_member_cannot_create_task_for_foreign_deal(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    from fastapi import Depends, Header

    from mini_crm.app.main import app
    from mini_crm.core.dependencies import get_db_session, get_request_context, get_request_user
    from mini_crm.modules.common.context import OrganizationContext, RequestContext, RequestUser
    from mini_crm.modules.organizations.repositories.sqlalchemy import (
        SQLAlchemyOrganizationRepository,
    )

    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1, role=UserRole.OWNER)

    # Create second user with MEMBER role
    member_user = User(
        id=2,
        email="member@example.com",
        hashed_password="hashed",
        name="Member",
        created_at=datetime.now(tz=UTC),
    )
    db_session.add(member_user)
    await db_session.commit()
    await seed_organization_member(db_session, user_id=2, organization_id=1, role=UserRole.MEMBER)

    # Create contact and deal owned by user 1
    await seed_contact(db_session, organization_id=1, owner_id=1)
    deal = await seed_deal(db_session, organization_id=1, contact_id=1, owner_id=1)

    async def override_get_request_user() -> RequestUser:
        return RequestUser(id=2, email="member@example.com", role=UserRole.MEMBER)

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
        payload = {
            "deal_id": deal.id,
            "title": "Member tries foreign deal",
            "description": "Should be forbidden",
            "due_date": "2025-12-31T00:00:00Z",
        }
        member_headers = {"Authorization": "Bearer test", "X-Organization-Id": "1"}
        response = await api_client.post("/api/v1/tasks", json=payload, headers=member_headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "You can only create tasks for your own deals"
    finally:
        app.dependency_overrides.pop(get_request_user, None)
        app.dependency_overrides.pop(get_request_context, None)


@pytest.mark.asyncio
async def test_create_task_for_deal_in_another_organization_forbidden(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1, role=UserRole.OWNER)

    # Create second organization and related contact/deal
    org2 = Organization(id=2, name="Beta Inc", created_at=datetime.now(tz=UTC))
    db_session.add(org2)
    await db_session.commit()

    contact_org2 = Contact(
        id=2,
        organization_id=2,
        owner_id=1,
        name="Org2 Contact",
        email="org2@example.com",
        phone="+222222",
        created_at=datetime.now(tz=UTC),
    )
    db_session.add(contact_org2)
    await db_session.commit()
    await db_session.refresh(contact_org2)

    deal_org2 = Deal(
        id=2,
        organization_id=2,
        contact_id=contact_org2.id,
        owner_id=1,
        title="Org2 Deal",
        amount=5000.00,
        currency="USD",
        status=DealStatus.NEW,
        stage=DealStage.QUALIFICATION,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    db_session.add(deal_org2)
    await db_session.commit()
    await db_session.refresh(deal_org2)

    payload = {
        "deal_id": deal_org2.id,
        "title": "Cross org task",
        "description": "Should fail",
        "due_date": "2025-12-31T00:00:00Z",
    }
    response = await api_client.post("/api/v1/tasks", json=payload, headers=HEADERS)
    assert response.status_code == 404
    assert "Deal not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_tasks_filters_by_deal_and_only_open(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1, role=UserRole.OWNER)
    contact = await seed_contact(db_session, organization_id=1, owner_id=1)

    now = datetime.now(tz=UTC)
    deal_one = Deal(
        organization_id=1,
        contact_id=contact.id,
        owner_id=1,
        title="Deal One",
        amount=1000,
        currency="USD",
        status=DealStatus.NEW,
        stage=DealStage.QUALIFICATION,
        created_at=now,
        updated_at=now,
    )
    deal_two = Deal(
        organization_id=1,
        contact_id=contact.id,
        owner_id=1,
        title="Deal Two",
        amount=2000,
        currency="USD",
        status=DealStatus.NEW,
        stage=DealStage.QUALIFICATION,
        created_at=now,
        updated_at=now,
    )
    db_session.add_all([deal_one, deal_two])
    await db_session.commit()
    await db_session.refresh(deal_one)
    await db_session.refresh(deal_two)

    tasks = [
        Task(
            deal_id=deal_one.id,
            title="Deal One Open",
            description=None,
            due_date=now + timedelta(days=1),
            is_done=False,
        ),
        Task(
            deal_id=deal_one.id,
            title="Deal One Done",
            description=None,
            due_date=now + timedelta(days=2),
            is_done=True,
        ),
        Task(
            deal_id=deal_two.id,
            title="Deal Two Open",
            description=None,
            due_date=now + timedelta(days=3),
            is_done=False,
        ),
    ]
    db_session.add_all(tasks)
    await db_session.commit()

    response = await api_client.get(
        "/api/v1/tasks",
        params={"deal_id": deal_one.id, "only_open": "true"},
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Deal One Open"
    assert data[0]["deal_id"] == deal_one.id


@pytest.mark.asyncio
async def test_list_tasks_filters_by_due_range(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1, role=UserRole.OWNER)
    await seed_contact(db_session, organization_id=1, owner_id=1)
    deal = await seed_deal(db_session, organization_id=1, contact_id=1, owner_id=1)

    now = datetime.now(tz=UTC)
    tasks = [
        Task(
            deal_id=deal.id,
            title="Past Task",
            description=None,
            due_date=now - timedelta(days=1),
            is_done=False,
        ),
        Task(
            deal_id=deal.id,
            title="Window Task",
            description=None,
            due_date=now + timedelta(days=2),
            is_done=False,
        ),
        Task(
            deal_id=deal.id,
            title="Future Task",
            description=None,
            due_date=now + timedelta(days=10),
            is_done=False,
        ),
        Task(
            deal_id=deal.id,
            title="No Due Date",
            description=None,
            due_date=None,
            is_done=False,
        ),
    ]
    db_session.add_all(tasks)
    await db_session.commit()

    due_after = (now + timedelta(hours=12)).isoformat().replace("+00:00", "Z")
    due_before = (now + timedelta(days=5)).isoformat().replace("+00:00", "Z")
    response = await api_client.get(
        "/api/v1/tasks",
        params={"due_after": due_after, "due_before": due_before},
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Window Task"
