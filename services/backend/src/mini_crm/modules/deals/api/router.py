from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.activities.repositories.sqlalchemy import SQLAlchemyActivityRepository
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.deals.dto.schemas import DealCreate, DealResponse, DealUpdate, PaginatedDeals
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository
from mini_crm.modules.deals.repositories.sqlalchemy import SQLAlchemyDealRepository
from mini_crm.modules.deals.services.service import DealService
from mini_crm.shared.enums import DealStage, DealStatus

router = APIRouter(prefix="/deals", tags=["deals"])


def get_deal_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractDealRepository:
    return SQLAlchemyDealRepository(session=session)


def get_activity_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractActivityRepository:
    return SQLAlchemyActivityRepository(session=session)


def get_deal_service(
    repository: AbstractDealRepository = Depends(get_deal_repository),
    activity_repository: AbstractActivityRepository = Depends(get_activity_repository),
) -> DealService:
    return DealService(repository=repository, activity_repository=activity_repository)


@router.get("", response_model=PaginatedDeals)
async def list_deals(
    page: int = 1,
    page_size: int = Query(default=50, le=100),
    status: list[str] | None = Query(default=None),
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    stage: str | None = None,
    owner_id: int | None = None,
    order_by: str | None = Query(default=None, pattern="^(created_at|amount)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    context: RequestContext = Depends(get_request_context),
    service: DealService = Depends(get_deal_service),
) -> PaginatedDeals:
    # Convert string parameters to enums
    status_enums: list[DealStatus] | None = None
    if status:
        status_enums = [DealStatus(s) for s in status]

    stage_enum: DealStage | None = None
    if stage:
        stage_enum = DealStage(stage)

    return await service.list_deals(
        context,
        page=page,
        page_size=page_size,
        status=status_enums,
        min_amount=min_amount,
        max_amount=max_amount,
        stage=stage_enum,
        owner_id=owner_id,
        order_by=order_by,
        order=order,
    )


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
