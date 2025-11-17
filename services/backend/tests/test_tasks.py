from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.auth.models import OrganizationMember, User
from mini_crm.modules.contacts.models import Contact
from mini_crm.modules.deals.models import Deal
from mini_crm.modules.organizations.models import Organization
from mini_crm.shared.enums import ActivityType, DealStage, DealStatus, UserRole

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
