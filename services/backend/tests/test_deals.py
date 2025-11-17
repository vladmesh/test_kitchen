from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.auth.models import OrganizationMember, User
from mini_crm.modules.contacts.models import Contact
from mini_crm.modules.deals.dto.schemas import DealCreate, DealUpdate
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
    from mini_crm.modules.activities.repositories.repository import InMemoryActivityRepository
    from mini_crm.modules.common.context import OrganizationContext, RequestContext, RequestUser
    from mini_crm.modules.deals.services.service import DealService

    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
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

    activity_repo = InMemoryActivityRepository()
    service = DealService(repository=repository, activity_repository=activity_repo)
    context = RequestContext(
        user=RequestUser(id=1, email="owner@example.com", role=UserRole.OWNER),
        organization=OrganizationContext(organization_id=1, role=UserRole.OWNER),
    )

    update_payload = DealUpdate(status=DealStatus.WON)
    with pytest.raises(HTTPException) as exc_info:
        await service.update_deal(context, created.id, update_payload)
    assert exc_info.value.status_code == 400
    assert "Amount must be positive" in exc_info.value.detail


@pytest.mark.asyncio
async def test_deal_crud_flow(api_client: AsyncClient, db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
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
    await seed_organization_member(db_session, user_id=1, organization_id=1)
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
    await seed_organization_member(db_session, user_id=1, organization_id=1)
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
        await seed_organization_member(db_session, user_id=1, organization_id=1)
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


@pytest.mark.asyncio
async def test_deal_update_member_ownership_check(db_session: AsyncSession) -> None:
    from mini_crm.modules.activities.repositories.repository import InMemoryActivityRepository
    from mini_crm.modules.common.context import OrganizationContext, RequestContext, RequestUser
    from mini_crm.modules.deals.dto.schemas import DealUpdate
    from mini_crm.modules.deals.services.service import DealService

    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create second user
    from mini_crm.modules.auth.models import User

    user2 = User(
        id=2,
        email="member@example.com",
        hashed_password="hashed",
        name="Member",
        created_at=datetime.now(tz=UTC),
    )
    db_session.add(user2)
    await db_session.commit()

    # Create organization member with MEMBER role
    await seed_organization_member(db_session, user_id=2, organization_id=1, role=UserRole.MEMBER)

    repository = SQLAlchemyDealRepository(session=db_session)
    activity_repo = InMemoryActivityRepository()
    service = DealService(repository=repository, activity_repository=activity_repo)

    # Create deal owned by user 1
    payload = DealCreate(
        contact_id=1,
        title="Test Deal",
        amount=Decimal("1000.00"),
        currency="USD",
    )
    created = await repository.create(organization_id=1, owner_id=1, payload=payload)

    # Try to update deal owned by user 1 as user 2 (member) - should fail
    member_context = RequestContext(
        user=RequestUser(id=2, email="member@example.com", role=UserRole.MEMBER),
        organization=OrganizationContext(organization_id=1, role=UserRole.MEMBER),
    )
    update_payload = DealUpdate(status=DealStatus.IN_PROGRESS)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await service.update_deal(member_context, created.id, update_payload)
    assert exc_info.value.status_code == 403
    assert "You can only update your own deals" in exc_info.value.detail


@pytest.mark.asyncio
async def test_deal_update_member_can_update_own_deal(db_session: AsyncSession) -> None:
    from mini_crm.modules.activities.repositories.repository import InMemoryActivityRepository
    from mini_crm.modules.common.context import OrganizationContext, RequestContext, RequestUser
    from mini_crm.modules.deals.dto.schemas import DealUpdate
    from mini_crm.modules.deals.services.service import DealService

    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create second user
    from mini_crm.modules.auth.models import User

    user2 = User(
        id=2,
        email="member@example.com",
        hashed_password="hashed",
        name="Member",
        created_at=datetime.now(tz=UTC),
    )
    db_session.add(user2)
    await db_session.commit()

    # Create organization member with MEMBER role
    await seed_organization_member(db_session, user_id=2, organization_id=1, role=UserRole.MEMBER)

    repository = SQLAlchemyDealRepository(session=db_session)
    activity_repo = InMemoryActivityRepository()
    service = DealService(repository=repository, activity_repository=activity_repo)

    # Create deal owned by user 2
    payload = DealCreate(
        contact_id=1,
        title="Test Deal",
        amount=Decimal("1000.00"),
        currency="USD",
    )
    created = await repository.create(organization_id=1, owner_id=2, payload=payload)

    # Update deal owned by user 2 as user 2 (member) - should succeed
    member_context = RequestContext(
        user=RequestUser(id=2, email="member@example.com", role=UserRole.MEMBER),
        organization=OrganizationContext(organization_id=1, role=UserRole.MEMBER),
    )
    update_payload = DealUpdate(status=DealStatus.IN_PROGRESS)
    updated = await service.update_deal(member_context, created.id, update_payload)
    assert updated.status == DealStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_deals_list_filter_by_status(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create deals with different statuses
    deal_ids = []
    for status in [DealStatus.NEW, DealStatus.IN_PROGRESS, DealStatus.WON]:
        create_payload = {
            "contact_id": 1,
            "title": f"Deal {status.value}",
            "amount": "1000.00",
            "currency": "USD",
        }
        response = await api_client.post("/api/v1/deals", json=create_payload, headers=HEADERS)
        deal_ids.append(response.json()["id"])

    # Update statuses
    for deal_id, status in zip(
        deal_ids, [DealStatus.NEW, DealStatus.IN_PROGRESS, DealStatus.WON], strict=True
    ):
        update_payload = {"status": status.value}
        await api_client.patch(f"/api/v1/deals/{deal_id}", json=update_payload, headers=HEADERS)

    # Filter by single status
    response = await api_client.get("/api/v1/deals?status=new", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1
    assert all(item["status"] == DealStatus.NEW.value for item in data["items"])

    # Filter by multiple statuses
    response = await api_client.get("/api/v1/deals?status=new&status=in_progress", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 2
    assert all(
        item["status"] in [DealStatus.NEW.value, DealStatus.IN_PROGRESS.value]
        for item in data["items"]
    )


@pytest.mark.asyncio
async def test_deals_list_filter_by_amount(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create deals with different amounts
    amounts = ["500.00", "1500.00", "2500.00", "3500.00"]
    for amount in amounts:
        create_payload = {
            "contact_id": 1,
            "title": f"Deal {amount}",
            "amount": amount,
            "currency": "USD",
        }
        await api_client.post("/api/v1/deals", json=create_payload, headers=HEADERS)

    # Filter by min_amount
    response = await api_client.get("/api/v1/deals?min_amount=2000.00", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 2
    assert all(Decimal(item["amount"]) >= Decimal("2000.00") for item in data["items"])

    # Filter by max_amount
    response = await api_client.get("/api/v1/deals?max_amount=2000.00", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 2
    assert all(Decimal(item["amount"]) <= Decimal("2000.00") for item in data["items"])

    # Filter by both min_amount and max_amount
    response = await api_client.get(
        "/api/v1/deals?min_amount=1000.00&max_amount=3000.00", headers=HEADERS
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 2
    assert all(
        Decimal("1000.00") <= Decimal(item["amount"]) <= Decimal("3000.00")
        for item in data["items"]
    )


@pytest.mark.asyncio
async def test_deals_list_filter_by_stage(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    repository = SQLAlchemyDealRepository(session=db_session)

    # Create deals with different stages
    for stage in [DealStage.QUALIFICATION, DealStage.PROPOSAL, DealStage.NEGOTIATION]:
        payload = DealCreate(
            contact_id=1,
            title=f"Deal {stage.value}",
            amount=Decimal("1000.00"),
            currency="USD",
        )
        created = await repository.create(organization_id=1, owner_id=1, payload=payload)
        await repository.update(
            organization_id=1, deal_id=created.id, payload=DealUpdate(stage=stage)
        )
        await db_session.commit()

    # Filter by stage
    response = await api_client.get("/api/v1/deals?stage=qualification", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1
    assert all(item["stage"] == DealStage.QUALIFICATION.value for item in data["items"])


@pytest.mark.asyncio
async def test_deals_list_filter_by_owner_id(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create second user
    from mini_crm.modules.auth.models import User

    user2 = User(
        id=2,
        email="user2@example.com",
        hashed_password="hashed",
        name="User 2",
        created_at=datetime.now(tz=UTC),
    )
    db_session.add(user2)
    await db_session.commit()
    await seed_organization_member(db_session, user_id=2, organization_id=1)

    repository = SQLAlchemyDealRepository(session=db_session)

    # Create deals for different owners
    payload1 = DealCreate(contact_id=1, title="Deal 1", amount=Decimal("1000.00"), currency="USD")
    await repository.create(organization_id=1, owner_id=1, payload=payload1)
    await db_session.commit()

    payload2 = DealCreate(contact_id=1, title="Deal 2", amount=Decimal("2000.00"), currency="USD")
    await repository.create(organization_id=1, owner_id=2, payload=payload2)
    await db_session.commit()

    # Filter by owner_id
    response = await api_client.get("/api/v1/deals?owner_id=1", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1
    assert all(item["owner_id"] == 1 for item in data["items"])


@pytest.mark.asyncio
async def test_deals_list_filter_by_owner_id_member_forbidden(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1, role=UserRole.MEMBER)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Try to filter by owner_id as member - should fail
    response = await api_client.get("/api/v1/deals?owner_id=1", headers=HEADERS)
    assert response.status_code == 403
    assert "Filtering by owner_id is not allowed for member role" in response.json()["detail"]


@pytest.mark.asyncio
async def test_deals_list_sort_by_created_at(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    repository = SQLAlchemyDealRepository(session=db_session)

    # Create deals with delays to ensure different created_at
    import asyncio

    for i in range(3):
        payload = DealCreate(
            contact_id=1,
            title=f"Deal {i}",
            amount=Decimal("1000.00"),
            currency="USD",
        )
        await repository.create(organization_id=1, owner_id=1, payload=payload)
        await db_session.commit()
        await asyncio.sleep(0.01)  # Small delay to ensure different timestamps

    # Sort by created_at ascending
    response = await api_client.get("/api/v1/deals?order_by=created_at&order=asc", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 3
    created_ats = [item.get("created_at") for item in data["items"] if "created_at" in item]
    if created_ats:
        assert created_ats == sorted(created_ats)

    # Sort by created_at descending
    response = await api_client.get("/api/v1/deals?order_by=created_at&order=desc", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    created_ats = [item.get("created_at") for item in data["items"] if "created_at" in item]
    if created_ats:
        assert created_ats == sorted(created_ats, reverse=True)


@pytest.mark.asyncio
async def test_deals_list_sort_by_amount(api_client: AsyncClient, db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create deals with different amounts
    amounts = ["3000.00", "1000.00", "2000.00"]
    for amount in amounts:
        create_payload = {
            "contact_id": 1,
            "title": f"Deal {amount}",
            "amount": amount,
            "currency": "USD",
        }
        await api_client.post("/api/v1/deals", json=create_payload, headers=HEADERS)

    # Sort by amount ascending
    response = await api_client.get("/api/v1/deals?order_by=amount&order=asc", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 3
    amounts_sorted = [Decimal(item["amount"]) for item in data["items"]]
    assert amounts_sorted == sorted(amounts_sorted)

    # Sort by amount descending
    response = await api_client.get("/api/v1/deals?order_by=amount&order=desc", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    amounts_sorted = [Decimal(item["amount"]) for item in data["items"]]
    assert amounts_sorted == sorted(amounts_sorted, reverse=True)


@pytest.mark.asyncio
async def test_deals_list_combined_filters(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    repository = SQLAlchemyDealRepository(session=db_session)

    # Create deals with different combinations
    payload1 = DealCreate(contact_id=1, title="Deal 1", amount=Decimal("1000.00"), currency="USD")
    deal1 = await repository.create(organization_id=1, owner_id=1, payload=payload1)
    await repository.update(
        organization_id=1,
        deal_id=deal1.id,
        payload=DealUpdate(status=DealStatus.NEW, stage=DealStage.QUALIFICATION),
    )
    await db_session.commit()

    payload2 = DealCreate(contact_id=1, title="Deal 2", amount=Decimal("2000.00"), currency="USD")
    deal2 = await repository.create(organization_id=1, owner_id=1, payload=payload2)
    await repository.update(
        organization_id=1,
        deal_id=deal2.id,
        payload=DealUpdate(status=DealStatus.IN_PROGRESS, stage=DealStage.PROPOSAL),
    )
    await db_session.commit()

    payload3 = DealCreate(contact_id=1, title="Deal 3", amount=Decimal("3000.00"), currency="USD")
    deal3 = await repository.create(organization_id=1, owner_id=1, payload=payload3)
    await repository.update(
        organization_id=1,
        deal_id=deal3.id,
        payload=DealUpdate(status=DealStatus.NEW, stage=DealStage.QUALIFICATION),
    )
    await db_session.commit()

    # Combine filters: status=NEW, min_amount=1500, stage=qualification
    response = await api_client.get(
        "/api/v1/deals?status=new&min_amount=1500.00&stage=qualification",
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] == 1
    assert data["items"][0]["title"] == "Deal 3"
