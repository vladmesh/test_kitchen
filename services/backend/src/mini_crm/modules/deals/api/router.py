from __future__ import annotations

from fastapi import APIRouter, Depends

from mini_crm.core.dependencies import get_request_context
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.deals.dto.schemas import DealCreate, DealResponse, DealUpdate, PaginatedDeals
from mini_crm.modules.deals.repositories.repository import InMemoryDealRepository
from mini_crm.modules.deals.services.service import DealService

router = APIRouter(prefix="/deals", tags=["deals"])


_deals_repository = InMemoryDealRepository()
_deals_service = DealService(repository=_deals_repository)


def get_deal_service() -> DealService:
    return _deals_service


@router.get("", response_model=PaginatedDeals)
async def list_deals(
    page: int = 1,
    page_size: int = 50,
    context: RequestContext = Depends(get_request_context),
    service: DealService = Depends(get_deal_service),
) -> PaginatedDeals:
    return await service.list_deals(context, page=page, page_size=page_size)


@router.post("", response_model=DealResponse, status_code=201)
async def create_deal(
    payload: DealCreate,
    context: RequestContext = Depends(get_request_context),
    service: DealService = Depends(get_deal_service),
) -> DealResponse:
    return await service.create_deal(context, payload)


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: int,
    payload: DealUpdate,
    context: RequestContext = Depends(get_request_context),
    service: DealService = Depends(get_deal_service),
) -> DealResponse:
    return await service.update_deal(context, deal_id, payload)
