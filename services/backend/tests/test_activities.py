from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.security import create_access_token
from mini_crm.modules.auth.models import OrganizationMember, User
from mini_crm.modules.contacts.models import Contact
from mini_crm.modules.deals.models import Deal
from mini_crm.modules.organizations.models import Organization
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
async def test_create_comment_activity_via_api(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)
    deal = await seed_deal(db_session, organization_id=1, contact_id=1, owner_id=1)

    # Create comment activity via API
    create_payload = {
        "type": ActivityType.COMMENT.value,
        "payload": {"text": "This is a test comment"},
    }
    create_response = await api_client.post(
        f"/api/v1/deals/{deal.id}/activities",
        json=create_payload,
        headers=HEADERS,
    )
    assert create_response.status_code == 201
    activity_data = create_response.json()
    assert activity_data["type"] == ActivityType.COMMENT.value
    assert activity_data["payload"] == {"text": "This is a test comment"}
    assert activity_data["author_id"] == 1
    assert activity_data["deal_id"] == deal.id

    # Verify activity is listed
    list_response = await api_client.get(
        f"/api/v1/deals/{deal.id}/activities",
        headers=HEADERS,
    )
    assert list_response.status_code == 200
    activities = list_response.json()
    assert len(activities) == 1
    assert activities[0]["type"] == ActivityType.COMMENT.value


@pytest.mark.asyncio
async def test_create_activity_rejects_non_comment_types(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)
    deal = await seed_deal(db_session, organization_id=1, contact_id=1, owner_id=1)

    # Try to create status_changed activity - should be rejected
    create_payload = {
        "type": ActivityType.STATUS_CHANGED.value,
        "payload": {"old_status": "new", "new_status": "won"},
    }
    response = await api_client.post(
        f"/api/v1/deals/{deal.id}/activities",
        json=create_payload,
        headers=HEADERS,
    )
    assert response.status_code == 400
    assert "Only comment activities can be created via API" in response.json()["detail"]

    # Try to create stage_changed activity - should be rejected
    create_payload = {
        "type": ActivityType.STAGE_CHANGED.value,
        "payload": {"old_stage": "qualification", "new_stage": "proposal"},
    }
    response = await api_client.post(
        f"/api/v1/deals/{deal.id}/activities",
        json=create_payload,
        headers=HEADERS,
    )
    assert response.status_code == 400
    assert "Only comment activities can be created via API" in response.json()["detail"]

    # Try to create task_created activity - should be rejected
    create_payload = {
        "type": ActivityType.TASK_CREATED.value,
        "payload": {"task_id": 1, "task_title": "Test task"},
    }
    response = await api_client.post(
        f"/api/v1/deals/{deal.id}/activities",
        json=create_payload,
        headers=HEADERS,
    )
    assert response.status_code == 400
    assert "Only comment activities can be created via API" in response.json()["detail"]

    # Try to create system activity - should be rejected
    create_payload = {
        "type": ActivityType.SYSTEM.value,
        "payload": {"message": "System event"},
    }
    response = await api_client.post(
        f"/api/v1/deals/{deal.id}/activities",
        json=create_payload,
        headers=HEADERS,
    )
    assert response.status_code == 400
    assert "Only comment activities can be created via API" in response.json()["detail"]
