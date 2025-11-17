from __future__ import annotations

from fastapi import HTTPException, status

from mini_crm.modules.activities.dto.schemas import ActivityCreate
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.deals.dto.schemas import DealCreate, DealResponse, DealUpdate, PaginatedDeals
from mini_crm.modules.deals.repositories.repository import (
    AbstractDealRepository,
    InMemoryDealRepository,
)
from mini_crm.modules.deals.repositories.sqlalchemy import SQLAlchemyDealRepository
from mini_crm.shared.dto.pagination import PaginationMeta
from mini_crm.shared.enums import ActivityType, DealStage, DealStatus, UserRole


class DealService:
    def __init__(
        self,
        repository: AbstractDealRepository | None = None,
        activity_repository: AbstractActivityRepository | None = None,
    ) -> None:
        self.repository = repository or InMemoryDealRepository()
        self.activity_repository = activity_repository

    async def list_deals(
        self, context: RequestContext, page: int, page_size: int
    ) -> PaginatedDeals:
        items, total = await self.repository.list(
            context.organization.organization_id, page=page, page_size=page_size
        )
        meta = PaginationMeta(page=page, page_size=page_size, total=total)
        return PaginatedDeals(items=items, meta=meta)

    async def create_deal(self, context: RequestContext, payload: DealCreate) -> DealResponse:
        return await self.repository.create(
            context.organization.organization_id, context.user.id, payload
        )

    def _get_stage_order(self, stage: DealStage) -> int:
        stage_order = [
            DealStage.QUALIFICATION,
            DealStage.PROPOSAL,
            DealStage.NEGOTIATION,
            DealStage.CLOSED,
        ]
        return stage_order.index(stage)

    def _is_stage_rollback(self, old_stage: DealStage, new_stage: DealStage) -> bool:
        return self._get_stage_order(new_stage) < self._get_stage_order(old_stage)

    async def update_deal(
        self, context: RequestContext, deal_id: int, payload: DealUpdate
    ) -> DealResponse:
        # Get current deal to check old values
        if isinstance(self.repository, SQLAlchemyDealRepository):
            old_deal = await self.repository.get_by_id(
                context.organization.organization_id, deal_id
            )
            if old_deal is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Deal not found",
                )
            old_status = old_deal.status
            old_stage = old_deal.stage
        else:
            # Fallback for InMemory repository (shouldn't happen in production)
            old_status = DealStatus.NEW
            old_stage = DealStage.QUALIFICATION

        update_data = payload.model_dump(exclude_none=True)
        new_status = update_data.get("status")
        new_stage = update_data.get("stage")

        # Normalize enum values to strings for comparison
        old_status_str = old_status.value if isinstance(old_status, DealStatus) else str(old_status)
        old_stage_str = old_stage.value if isinstance(old_stage, DealStage) else str(old_stage)
        new_status_str = (
            new_status.value
            if isinstance(new_status, DealStatus)
            else (str(new_status) if new_status else None)
        )
        new_stage_str = (
            new_stage.value
            if isinstance(new_stage, DealStage)
            else (str(new_stage) if new_stage else None)
        )

        # Check stage rollback permission
        if new_stage is not None and new_stage_str != old_stage_str:
            # Convert to enum for comparison
            old_stage_enum = (
                DealStage(old_stage_str) if isinstance(old_stage_str, str) else old_stage
            )
            new_stage_enum = (
                DealStage(new_stage_str) if isinstance(new_stage_str, str) else new_stage
            )
            if self._is_stage_rollback(old_stage_enum, new_stage_enum):
                if context.organization.role not in {UserRole.ADMIN, UserRole.OWNER}:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Stage rollback is not allowed for your role",
                    )

        # Update deal
        updated_deal = await self.repository.update(
            context.organization.organization_id, deal_id, payload
        )

        # Create Activity records for status/stage changes
        if self.activity_repository is not None:
            if new_status is not None and new_status_str != old_status_str:
                activity_payload = ActivityCreate(
                    type=ActivityType.STATUS_CHANGED,
                    payload={"old_status": old_status_str, "new_status": new_status_str},
                )
                await self.activity_repository.create(
                    context.organization.organization_id,
                    deal_id,
                    activity_payload,
                )

            if new_stage is not None and new_stage_str != old_stage_str:
                activity_payload = ActivityCreate(
                    type=ActivityType.STAGE_CHANGED,
                    payload={"old_stage": old_stage_str, "new_stage": new_stage_str},
                )
                await self.activity_repository.create(
                    context.organization.organization_id,
                    deal_id,
                    activity_payload,
                )

        return updated_deal
