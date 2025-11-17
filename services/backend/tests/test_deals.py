from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.auth.models import User
from mini_crm.modules.contacts.models import Contact
from mini_crm.modules.deals.dto.schemas import DealCreate
from mini_crm.modules.deals.repositories.sqlalchemy import SQLAlchemyDealRepository
from mini_crm.modules.organizations.models import Organization
from mini_crm.shared.enums import DealStage, DealStatus, UserRole

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
async def test_sqlalchemy_deal_repository(db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)
    repository = SQLAlchemyDealRepository(session=db_session)

    payload = DealCreate(
        contact_id=1,
        title="Test Deal",
        amount=Decimal("1000.00"),
        currency="USD",
    )
    created = await repository.create(organization_id=1, owner_id=1, payload=payload)

    assert created.id == 1
    assert created.owner_id == 1
    assert created.contact_id == 1
    assert created.title == "Test Deal"
    assert created.amount == Decimal("1000.00")
    assert created.status == DealStatus.NEW
    assert created.stage == DealStage.QUALIFICATION

    items, total = await repository.list(organization_id=1, page=1, page_size=10)
    assert total == 1
    assert items[0].title == "Test Deal"


@pytest.mark.asyncio
async def test_deal_repository_contact_validation(db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    repository = SQLAlchemyDealRepository(session=db_session)

    payload = DealCreate(
        contact_id=999,  # Non-existent contact
        title="Test Deal",
        amount=Decimal("1000.00"),
        currency="USD",
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await repository.create(organization_id=1, owner_id=1, payload=payload)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_deal_repository_update(db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)
    repository = SQLAlchemyDealRepository(session=db_session)

    payload = DealCreate(
        contact_id=1,
        title="Test Deal",
        amount=Decimal("1000.00"),
        currency="USD",
    )
    created = await repository.create(organization_id=1, owner_id=1, payload=payload)

    from mini_crm.modules.deals.dto.schemas import DealUpdate

    update_payload = DealUpdate(status=DealStatus.WON)
    updated = await repository.update(organization_id=1, deal_id=created.id, payload=update_payload)

    assert updated.status == DealStatus.WON
    assert updated.id == created.id


@pytest.mark.asyncio
async def test_deal_repository_update_won_with_zero_amount(db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)
    repository = SQLAlchemyDealRepository(session=db_session)

    payload = DealCreate(
        contact_id=1,
        title="Test Deal",
        amount=Decimal("0.00"),
        currency="USD",
    )
    created = await repository.create(organization_id=1, owner_id=1, payload=payload)

    from fastapi import HTTPException

    from mini_crm.modules.deals.dto.schemas import DealUpdate

    update_payload = DealUpdate(status=DealStatus.WON)
    with pytest.raises(HTTPException) as exc_info:
        await repository.update(organization_id=1, deal_id=created.id, payload=update_payload)
    assert exc_info.value.status_code == 400
    assert "Amount must be positive" in exc_info.value.detail


@pytest.mark.asyncio
async def test_deal_crud_flow(api_client: AsyncClient, db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    create_payload = {
        "contact_id": 1,
        "title": "Website redesign",
        "amount": "10000.00",
        "currency": "EUR",
    }
    create_response = await api_client.post(
        "/api/v1/deals",
        json=create_payload,
        headers=HEADERS,
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["title"] == "Website redesign"
    assert body["amount"] == "10000.00"
    assert body["status"] == DealStatus.NEW.value

    list_response = await api_client.get("/api/v1/deals", headers=HEADERS)
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["meta"]["total"] == 1
    assert data["items"][0]["title"] == "Website redesign"


@pytest.mark.asyncio
async def test_deal_update_status(api_client: AsyncClient, db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create deal
    create_payload = {
        "contact_id": 1,
        "title": "Test Deal",
        "amount": "5000.00",
        "currency": "USD",
    }
    create_response = await api_client.post(
        "/api/v1/deals",
        json=create_payload,
        headers=HEADERS,
    )
    deal_id = create_response.json()["id"]

    # Update status to WON
    update_payload = {"status": DealStatus.WON.value}
    update_response = await api_client.patch(
        f"/api/v1/deals/{deal_id}",
        json=update_payload,
        headers=HEADERS,
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == DealStatus.WON.value


@pytest.mark.asyncio
async def test_deal_update_won_with_zero_amount(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create deal with zero amount
    create_payload = {
        "contact_id": 1,
        "title": "Test Deal",
        "amount": "0.00",
        "currency": "USD",
    }
    create_response = await api_client.post(
        "/api/v1/deals",
        json=create_payload,
        headers=HEADERS,
    )
    deal_id = create_response.json()["id"]

    # Try to update status to WON - should fail
    update_payload = {"status": DealStatus.WON.value}
    update_response = await api_client.patch(
        f"/api/v1/deals/{deal_id}",
        json=update_payload,
        headers=HEADERS,
    )
    assert update_response.status_code == 400
    assert "Amount must be positive" in update_response.json()["detail"]


@pytest.mark.asyncio
async def test_deal_update_creates_activity(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    from mini_crm.app.main import app
    from mini_crm.modules.activities.repositories.repository import InMemoryActivityRepository
    from mini_crm.modules.deals.api.router import get_activity_repository

    # Use shared activity repository instance
    shared_activity_repo = InMemoryActivityRepository()
    app.dependency_overrides[get_activity_repository] = lambda: shared_activity_repo

    try:
        await seed_user_and_org(db_session)
        await seed_contact(db_session, organization_id=1, owner_id=1)

        # Create deal
        create_payload = {
            "contact_id": 1,
            "title": "Test Deal",
            "amount": "5000.00",
            "currency": "USD",
        }
        create_response = await api_client.post(
            "/api/v1/deals",
            json=create_payload,
            headers=HEADERS,
        )
        deal_id = create_response.json()["id"]

        # Update status - should create activity
        update_payload = {"status": DealStatus.WON.value}
        update_response = await api_client.patch(
            f"/api/v1/deals/{deal_id}",
            json=update_payload,
            headers=HEADERS,
        )
        assert update_response.status_code == 200

        # Check activities using the same repository instance
        activities = await shared_activity_repo.list(organization_id=1, deal_id=deal_id)
        assert len(activities) == 1
        assert activities[0].type.value == "status_changed"
        assert activities[0].payload is not None
        assert activities[0].payload["new_status"] == DealStatus.WON.value
    finally:
        app.dependency_overrides.pop(get_activity_repository, None)


@pytest.mark.asyncio
async def test_deal_stage_rollback_permission(db_session: AsyncSession) -> None:
    from mini_crm.modules.activities.repositories.repository import InMemoryActivityRepository
    from mini_crm.modules.common.context import OrganizationContext, RequestContext, RequestUser
    from mini_crm.modules.deals.dto.schemas import DealUpdate
    from mini_crm.modules.deals.services.service import DealService

    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    repository = SQLAlchemyDealRepository(session=db_session)
    activity_repo = InMemoryActivityRepository()
    service = DealService(repository=repository, activity_repository=activity_repo)

    # Create deal
    payload = DealCreate(
        contact_id=1,
        title="Test Deal",
        amount=Decimal("1000.00"),
        currency="USD",
    )
    created = await repository.create(organization_id=1, owner_id=1, payload=payload)

    # Move to PROPOSAL stage
    update_payload = DealUpdate(stage=DealStage.PROPOSAL)
    await repository.update(organization_id=1, deal_id=created.id, payload=update_payload)

    # Try to rollback to QUALIFICATION as MEMBER - should fail
    member_context = RequestContext(
        user=RequestUser(id=1, email="member@example.com", role=UserRole.MEMBER),
        organization=OrganizationContext(organization_id=1, role=UserRole.MEMBER),
    )
    rollback_payload = DealUpdate(stage=DealStage.QUALIFICATION)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await service.update_deal(member_context, created.id, rollback_payload)
    assert exc_info.value.status_code == 403
    assert "Stage rollback is not allowed" in exc_info.value.detail

    # Try as ADMIN - should succeed
    admin_context = RequestContext(
        user=RequestUser(id=1, email="admin@example.com", role=UserRole.ADMIN),
        organization=OrganizationContext(organization_id=1, role=UserRole.ADMIN),
    )
    updated = await service.update_deal(admin_context, created.id, rollback_payload)
    assert updated.stage == DealStage.QUALIFICATION
