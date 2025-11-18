from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.contacts.domain.exceptions import ContactNotFoundError
from mini_crm.modules.contacts.models import Contact
from mini_crm.modules.deals.domain.exceptions import DealNotFoundError
from mini_crm.modules.deals.dto.schemas import DealCreate, DealResponse, DealUpdate
from mini_crm.modules.deals.models import Deal
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository
from mini_crm.shared.enums import DealStage, DealStatus


class SQLAlchemyDealRepository(AbstractDealRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        organization_id: int,
        *,
        page: int,
        page_size: int,
        status: list[DealStatus] | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        stage: DealStage | None = None,
        owner_id: int | None = None,
        order_by: str | None = None,
        order: str = "asc",
    ) -> tuple[list[DealResponse], int]:
        offset = max(page - 1, 0) * page_size

        # Build base query with filters
        stmt = select(Deal).where(Deal.organization_id == organization_id)

        # Apply filters
        if status:
            stmt = stmt.where(Deal.status.in_(status))
        if min_amount is not None:
            stmt = stmt.where(Deal.amount >= min_amount)
        if max_amount is not None:
            stmt = stmt.where(Deal.amount <= max_amount)
        if stage is not None:
            stmt = stmt.where(Deal.stage == stage)
        if owner_id is not None:
            stmt = stmt.where(Deal.owner_id == owner_id)

        # Apply sorting
        if order_by == "created_at":
            if order == "desc":
                stmt = stmt.order_by(Deal.created_at.desc())
            else:
                stmt = stmt.order_by(Deal.created_at.asc())
        elif order_by == "amount":
            if order == "desc":
                stmt = stmt.order_by(Deal.amount.desc())
            else:
                stmt = stmt.order_by(Deal.amount.asc())
        else:
            if order == "desc":
                stmt = stmt.order_by(Deal.id.desc())
            else:
                stmt = stmt.order_by(Deal.id.asc())

        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.scalars(stmt)
        deals = result.all()

        # Build count query with same filters
        count_stmt = (
            select(func.count()).select_from(Deal).where(Deal.organization_id == organization_id)
        )

        if status:
            count_stmt = count_stmt.where(Deal.status.in_(status))
        if min_amount is not None:
            count_stmt = count_stmt.where(Deal.amount >= min_amount)
        if max_amount is not None:
            count_stmt = count_stmt.where(Deal.amount <= max_amount)
        if stage is not None:
            count_stmt = count_stmt.where(Deal.stage == stage)
        if owner_id is not None:
            count_stmt = count_stmt.where(Deal.owner_id == owner_id)

        total = await self.session.scalar(count_stmt)

        items = [DealResponse.model_validate(deal) for deal in deals]
        return items, int(total or 0)

    async def create(
        self, organization_id: int, owner_id: int, payload: DealCreate
    ) -> DealResponse:
        # Check if contact exists and belongs to organization
        contact_stmt = select(Contact).where(
            Contact.id == payload.contact_id,
            Contact.organization_id == organization_id,
        )
        contact = await self.session.scalar(contact_stmt)
        if contact is None:
            raise ContactNotFoundError(payload.contact_id)

        deal = Deal(
            organization_id=organization_id,
            contact_id=payload.contact_id,
            owner_id=owner_id,
            title=payload.title,
            amount=payload.amount,
            currency=payload.currency,
            status=DealStatus.NEW,
            stage=DealStage.QUALIFICATION,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        self.session.add(deal)
        await self.session.flush()
        await self.session.refresh(deal)
        return DealResponse.model_validate(deal)

    async def update(self, organization_id: int, deal_id: int, payload: DealUpdate) -> DealResponse:
        stmt = select(Deal).where(
            Deal.id == deal_id,
            Deal.organization_id == organization_id,
        )
        deal = await self.session.scalar(stmt)
        if deal is None:
            raise DealNotFoundError(deal_id)

        # Update fields
        update_data = payload.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(deal, key, value)

        deal.updated_at = datetime.now(tz=UTC)
        await self.session.flush()
        await self.session.refresh(deal)
        return DealResponse.model_validate(deal)

    async def get_by_id(self, organization_id: int, deal_id: int) -> DealResponse | None:
        stmt = select(Deal).where(
            Deal.id == deal_id,
            Deal.organization_id == organization_id,
        )
        result = await self.session.scalar(stmt)
        if result is None:
            return None
        return DealResponse.model_validate(result)

    async def has_deals_for_contact(self, contact_id: int) -> bool:
        """Check if contact has any deals."""
        stmt = select(func.count()).select_from(Deal).where(Deal.contact_id == contact_id)
        count = await self.session.scalar(stmt)
        return bool(count and count > 0)
