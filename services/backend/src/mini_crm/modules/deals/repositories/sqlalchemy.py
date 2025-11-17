from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.contacts.models import Contact
from mini_crm.modules.deals.dto.schemas import DealCreate, DealResponse, DealUpdate
from mini_crm.modules.deals.models import Deal
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository
from mini_crm.shared.enums import DealStage, DealStatus


class SQLAlchemyDealRepository(AbstractDealRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self, organization_id: int, *, page: int, page_size: int
    ) -> tuple[list[DealResponse], int]:
        offset = max(page - 1, 0) * page_size
        stmt = (
            select(Deal)
            .where(Deal.organization_id == organization_id)
            .order_by(Deal.id)
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.scalars(stmt)
        deals = result.all()

        count_stmt = (
            select(func.count()).select_from(Deal).where(Deal.organization_id == organization_id)
        )
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found or does not belong to organization",
            )

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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal not found",
            )

        # Validate amount > 0 for won status
        update_data = payload.model_dump(exclude_none=True)
        new_status = update_data.get("status", deal.status)
        if new_status == DealStatus.WON:
            amount_to_check = update_data.get("amount", deal.amount)
            if amount_to_check <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Amount must be positive for won deals",
                )

        # Update fields
        for key, value in update_data.items():
            setattr(deal, key, value)

        deal.updated_at = datetime.now(tz=UTC)
        await self.session.flush()
        await self.session.refresh(deal)
        return DealResponse.model_validate(deal)

    async def get_by_id(self, organization_id: int, deal_id: int) -> Deal | None:
        stmt = select(Deal).where(
            Deal.id == deal_id,
            Deal.organization_id == organization_id,
        )
        result = await self.session.scalar(stmt)
        return cast(Deal | None, result)
