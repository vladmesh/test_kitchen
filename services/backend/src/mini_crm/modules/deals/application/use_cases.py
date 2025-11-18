from __future__ import annotations

from decimal import Decimal

from mini_crm.modules.activities.dto.schemas import ActivityCreate
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.common.application.context import RequestContext
from mini_crm.modules.common.domain.services import PermissionService
from mini_crm.modules.deals.application.dto import DealListDTO
from mini_crm.modules.deals.domain.exceptions import (
    DealNotFoundError,
    DealPermissionDeniedError,
)
from mini_crm.modules.deals.domain.services import DealDomainService
from mini_crm.modules.deals.dto.schemas import DealCreate, DealResponse, DealUpdate
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository
from mini_crm.shared.enums import ActivityType, DealStage, DealStatus, UserRole


class ListDealsUseCase:
    """Use case for listing deals."""

    def __init__(self, repository: AbstractDealRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        context: RequestContext,
        page: int,
        page_size: int,
        status: list[DealStatus] | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        stage: DealStage | None = None,
        owner_id: int | None = None,
        order_by: str | None = None,
        order: str = "asc",
    ) -> DealListDTO:
        """List deals with permission checks."""
        if owner_id is not None:
            if not PermissionService.can_filter_by_owner(context.organization.role):
                raise DealPermissionDeniedError(
                    "Filtering by owner_id is not allowed for member role"
                )

        items, total = await self.repository.list(
            context.organization.organization_id,
            page=page,
            page_size=page_size,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            stage=stage,
            owner_id=owner_id,
            order_by=order_by,
            order=order,
        )
        return DealListDTO(items=items, total=total, page=page, page_size=page_size)


class CreateDealUseCase:
    """Use case for creating a deal."""

    def __init__(self, repository: AbstractDealRepository) -> None:
        self.repository = repository

    async def execute(self, context: RequestContext, payload: DealCreate) -> DealResponse:
        """Create a new deal."""
        deal = await self.repository.create(
            context.organization.organization_id, context.user.id, payload
        )
        return deal


class UpdateDealUseCase:
    """Use case for updating a deal."""

    def __init__(
        self,
        repository: AbstractDealRepository,
        activity_repository: AbstractActivityRepository | None = None,
    ) -> None:
        self.repository = repository
        self.activity_repository = activity_repository

    async def execute(
        self, context: RequestContext, deal_id: int, payload: DealUpdate
    ) -> DealResponse:
        """Update a deal with business rule validation."""
        # Get current deal to check old values
        old_deal = await self.repository.get_by_id(context.organization.organization_id, deal_id)
        if old_deal is None:
            raise DealNotFoundError(deal_id)

        # Check member ownership: member can only update their own deals
        if context.organization.role == UserRole.MEMBER:
            if old_deal.owner_id != context.user.id:
                raise DealPermissionDeniedError("You can only update your own deals")

        update_data = payload.model_dump(exclude_none=True)
        new_status = update_data.get("status")
        new_stage = update_data.get("stage")
        new_amount = update_data.get("amount")

        # Validate amount > 0 for won status
        if new_status == DealStatus.WON:
            amount_to_check = new_amount if new_amount is not None else old_deal.amount
            DealDomainService.validate_won_deal_amount(amount_to_check)

        # Check stage rollback permission
        if new_stage is not None and new_stage != old_deal.stage:
            DealDomainService.validate_stage_rollback(
                old_deal.stage, new_stage, context.organization.role
            )

        # Update deal
        updated_deal = await self.repository.update(
            context.organization.organization_id, deal_id, payload
        )

        # Create Activity records for status/stage changes
        if self.activity_repository is not None:
            if new_status is not None and new_status != old_deal.status:
                activity_payload = ActivityCreate(
                    type=ActivityType.STATUS_CHANGED,
                    payload={"old_status": old_deal.status.value, "new_status": new_status.value},
                )
                await self.activity_repository.create(
                    context.organization.organization_id,
                    deal_id,
                    activity_payload,
                    author_id=context.user.id,
                )

            if new_stage is not None and new_stage != old_deal.stage:
                activity_payload = ActivityCreate(
                    type=ActivityType.STAGE_CHANGED,
                    payload={"old_stage": old_deal.stage.value, "new_stage": new_stage.value},
                )
                await self.activity_repository.create(
                    context.organization.organization_id,
                    deal_id,
                    activity_payload,
                    author_id=context.user.id,
                )

        return updated_deal
