from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.activities.dto.schemas import ActivityCreate, ActivityResponse
from mini_crm.modules.activities.models import Activity
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.deals.models import Deal


class SQLAlchemyActivityRepository(AbstractActivityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, organization_id: int, deal_id: int) -> list[ActivityResponse]:
        # Join with Deal to ensure deal belongs to organization
        stmt = (
            select(Activity)
            .join(Deal, Activity.deal_id == Deal.id)
            .where(
                Activity.deal_id == deal_id,
                Deal.organization_id == organization_id,
            )
            .order_by(Activity.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        activities = result.all()

        return [ActivityResponse.model_validate(activity) for activity in activities]

    async def create(
        self,
        organization_id: int,
        deal_id: int,
        payload: ActivityCreate,
        author_id: int | None = None,
    ) -> ActivityResponse:
        # Check if deal exists and belongs to organization
        deal_stmt = select(Deal).where(
            Deal.id == deal_id,
            Deal.organization_id == organization_id,
        )
        deal = await self.session.scalar(deal_stmt)
        if deal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal not found",
            )

        activity = Activity(
            deal_id=deal_id,
            author_id=author_id,
            type=payload.type,
            payload=payload.payload,
        )
        self.session.add(activity)
        await self.session.flush()
        await self.session.refresh(activity)
        return ActivityResponse.model_validate(activity)
