from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.security import create_access_token
from mini_crm.modules.analytics.repositories.sqlalchemy import SQLAlchemyAnalyticsRepository
from mini_crm.modules.auth.models import OrganizationMember, User
from mini_crm.modules.contacts.models import Contact
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
        organization_id=organization_id,
        owner_id=owner_id,
        name="John Doe",
        email="john@example.com",
        phone="+111111",
        created_at=datetime.now(tz=UTC),
    )
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return contact


async def seed_deal(
    session: AsyncSession,
    organization_id: int,
    contact_id: int,
    owner_id: int,
    status: DealStatus = DealStatus.NEW,
    stage: DealStage = DealStage.QUALIFICATION,
    amount: Decimal = Decimal("1000.00"),
    created_at: datetime | None = None,
) -> Deal:
    if created_at is None:
        created_at = datetime.now(tz=UTC)
    deal = Deal(
        organization_id=organization_id,
        contact_id=contact_id,
        owner_id=owner_id,
        title="Test Deal",
        amount=amount,
        currency="USD",
        status=status,
        stage=stage,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(deal)
    await session.commit()
    await session.refresh(deal)
    return deal


@pytest.mark.asyncio
async def test_deals_summary_with_real_data(db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create deals with different statuses
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        status=DealStatus.NEW,
        amount=Decimal("1000.00"),
    )
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        status=DealStatus.IN_PROGRESS,
        amount=Decimal("2000.00"),
    )
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        status=DealStatus.WON,
        amount=Decimal("3000.00"),
    )
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        status=DealStatus.WON,
        amount=Decimal("5000.00"),
    )
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        status=DealStatus.LOST,
        amount=Decimal("1000.00"),
    )

    repository = SQLAlchemyAnalyticsRepository(session=db_session)
    summary = await repository.deals_summary(organization_id=1)

    assert summary.total_deals == 5
    assert summary.deals_by_status.new == 1
    assert summary.deals_by_status.in_progress == 1
    assert summary.deals_by_status.won == 2
    assert summary.deals_by_status.lost == 1

    assert summary.amounts_by_status.new == Decimal("1000.00")
    assert summary.amounts_by_status.in_progress == Decimal("2000.00")
    assert summary.amounts_by_status.won == Decimal("8000.00")
    assert summary.amounts_by_status.lost == Decimal("1000.00")

    assert summary.avg_won_amount == Decimal("4000.00")


@pytest.mark.asyncio
async def test_deals_summary_empty_organization(db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)

    repository = SQLAlchemyAnalyticsRepository(session=db_session)
    summary = await repository.deals_summary(organization_id=1)

    assert summary.total_deals == 0
    assert summary.deals_by_status.new == 0
    assert summary.deals_by_status.in_progress == 0
    assert summary.deals_by_status.won == 0
    assert summary.deals_by_status.lost == 0
    assert summary.avg_won_amount is None
    assert summary.new_deals_last_30_days == 0


@pytest.mark.asyncio
async def test_deals_summary_new_deals_last_30_days(db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create deal within last 30 days
    recent_date = datetime.now(tz=UTC) - timedelta(days=15)
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        status=DealStatus.NEW,
        created_at=recent_date,
    )

    # Create deal older than 30 days
    old_date = datetime.now(tz=UTC) - timedelta(days=35)
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        status=DealStatus.NEW,
        created_at=old_date,
    )

    repository = SQLAlchemyAnalyticsRepository(session=db_session)
    summary = await repository.deals_summary(organization_id=1)

    assert summary.new_deals_last_30_days == 1
    assert summary.deals_by_status.new == 2  # Total new deals


@pytest.mark.asyncio
async def test_deals_funnel_with_real_data(db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create deals at different stages
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        stage=DealStage.QUALIFICATION,
        status=DealStatus.NEW,
    )
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        stage=DealStage.QUALIFICATION,
        status=DealStatus.IN_PROGRESS,
    )
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        stage=DealStage.PROPOSAL,
        status=DealStatus.IN_PROGRESS,
    )
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        stage=DealStage.NEGOTIATION,
        status=DealStatus.WON,
    )
    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        stage=DealStage.CLOSED,
        status=DealStatus.WON,
    )

    repository = SQLAlchemyAnalyticsRepository(session=db_session)
    funnel = await repository.deals_funnel(organization_id=1)

    assert len(funnel.stages) == 4

    # Cumulative funnel: each stage includes all deals that reached this stage or later
    qualification = next(s for s in funnel.stages if s.stage == "qualification")
    assert (
        qualification.total == 5
    )  # 2 in Qualification + 1 in Proposal + 1 in Negotiation + 1 in Closed
    assert qualification.by_status.new == 1
    assert qualification.by_status.in_progress == 2  # 1 in Qualification + 1 in Proposal
    assert qualification.by_status.won == 2  # 1 in Negotiation + 1 in Closed

    proposal = next(s for s in funnel.stages if s.stage == "proposal")
    assert proposal.total == 3  # 1 in Proposal + 1 in Negotiation + 1 in Closed
    assert proposal.by_status.in_progress == 1
    assert proposal.by_status.won == 2  # 1 in Negotiation + 1 in Closed

    negotiation = next(s for s in funnel.stages if s.stage == "negotiation")
    assert negotiation.total == 2  # 1 in Negotiation + 1 in Closed
    assert negotiation.by_status.won == 2  # 1 in Negotiation + 1 in Closed

    closed = next(s for s in funnel.stages if s.stage == "closed")
    assert closed.total == 1
    assert closed.by_status.won == 1


@pytest.mark.asyncio
async def test_deals_funnel_conversion_rates(db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    # Create 10 deals at qualification stage
    for _ in range(10):
        await seed_deal(
            db_session,
            organization_id=1,
            contact_id=1,
            owner_id=1,
            stage=DealStage.QUALIFICATION,
            status=DealStatus.NEW,
        )

    # 5 move to proposal
    for _ in range(5):
        await seed_deal(
            db_session,
            organization_id=1,
            contact_id=1,
            owner_id=1,
            stage=DealStage.PROPOSAL,
            status=DealStatus.IN_PROGRESS,
        )

    # 3 move to negotiation
    for _ in range(3):
        await seed_deal(
            db_session,
            organization_id=1,
            contact_id=1,
            owner_id=1,
            stage=DealStage.NEGOTIATION,
            status=DealStatus.IN_PROGRESS,
        )

    # 2 move to closed
    for _ in range(2):
        await seed_deal(
            db_session,
            organization_id=1,
            contact_id=1,
            owner_id=1,
            stage=DealStage.CLOSED,
            status=DealStatus.WON,
        )

    repository = SQLAlchemyAnalyticsRepository(session=db_session)
    funnel = await repository.deals_funnel(organization_id=1)

    assert len(funnel.conversion_rates) == 3

    # Cumulative funnel conversion rates:
    # Qualification: 10 + 5 + 3 + 2 = 20 total
    # Proposal: 5 + 3 + 2 = 10 total
    # Negotiation: 3 + 2 = 5 total
    # Closed: 2 total

    # Qualification to Proposal: 10/20 = 50%
    qual_to_prop = next(
        cr
        for cr in funnel.conversion_rates
        if cr.from_stage == "qualification" and cr.to_stage == "proposal"
    )
    assert qual_to_prop.rate_percent == 50.0

    # Proposal to Negotiation: 5/10 = 50%
    prop_to_neg = next(
        cr
        for cr in funnel.conversion_rates
        if cr.from_stage == "proposal" and cr.to_stage == "negotiation"
    )
    assert prop_to_neg.rate_percent == 50.0

    # Negotiation to Closed: 2/5 = 40%
    neg_to_closed = next(
        cr
        for cr in funnel.conversion_rates
        if cr.from_stage == "negotiation" and cr.to_stage == "closed"
    )
    assert abs(neg_to_closed.rate_percent - 40.0) < 0.1


@pytest.mark.asyncio
async def test_analytics_api_summary(api_client: AsyncClient, db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        status=DealStatus.WON,
        amount=Decimal("5000.00"),
    )

    response = await api_client.get("/api/v1/analytics/deals/summary", headers=HEADERS)
    assert response.status_code == 200

    data = response.json()
    assert data["total_deals"] == 1
    assert data["deals_by_status"]["won"] == 1
    assert data["amounts_by_status"]["won"] == "5000.00"
    assert data["avg_won_amount"] == "5000.00"


@pytest.mark.asyncio
async def test_analytics_api_funnel(api_client: AsyncClient, db_session: AsyncSession) -> None:
    await seed_user_and_org(db_session)
    await seed_organization_member(db_session, user_id=1, organization_id=1)
    await seed_contact(db_session, organization_id=1, owner_id=1)

    await seed_deal(
        db_session,
        organization_id=1,
        contact_id=1,
        owner_id=1,
        stage=DealStage.QUALIFICATION,
        status=DealStatus.NEW,
    )

    response = await api_client.get("/api/v1/analytics/deals/funnel", headers=HEADERS)
    assert response.status_code == 200

    data = response.json()
    assert len(data["stages"]) == 4
    assert len(data["conversion_rates"]) == 3

    qualification = next(s for s in data["stages"] if s["stage"] == "qualification")
    assert (
        qualification["total"] == 1
    )  # Cumulative: 1 in Qualification (and no deals in later stages)
