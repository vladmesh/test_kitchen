from __future__ import annotations

from fastapi import HTTPException, status

from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.deals.dto.schemas import DealCreate, DealResponse, DealUpdate, PaginatedDeals
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository, InMemoryDealRepository
from mini_crm.shared.dto.pagination import PaginationMeta
from mini_crm.shared.enums import DealStatus


class DealService:
    def __init__(self, repository: AbstractDealRepository | None = None) -> None:
        self.repository = repository or InMemoryDealRepository()

    async def list_deals(self, context: RequestContext, page: int, page_size: int) -> PaginatedDeals:
        items, total = await self.repository.list(context.organization.organization_id, page=page, page_size=page_size)
        meta = PaginationMeta(page=page, page_size=page_size, total=total)
        return PaginatedDeals(items=items, meta=meta)

    async def create_deal(self, context: RequestContext, payload: DealCreate) -> DealResponse:
        return await self.repository.create(context.organization.organization_id, context.user.id, payload)

    async def update_deal(self, context: RequestContext, deal_id: int, payload: DealUpdate) -> DealResponse:
        data = payload.model_dump(exclude_none=True)
        if data.get("status") == DealStatus.WON and data.get("amount", 1) <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive for won deals")
        return await self.repository.update(context.organization.organization_id, deal_id, payload)
