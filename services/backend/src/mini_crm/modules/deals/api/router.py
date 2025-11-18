from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.activities.repositories.sqlalchemy import SQLAlchemyActivityRepository
from mini_crm.modules.common.application.context import RequestContext
from mini_crm.modules.deals.application.use_cases import (
    CreateDealUseCase,
    ListDealsUseCase,
    UpdateDealUseCase,
)
from mini_crm.modules.deals.domain.exceptions import (
    DealNotFoundError,
    DealPermissionDeniedError,
    DealValidationError,
)
from mini_crm.modules.deals.dto.schemas import DealCreate, DealResponse, DealUpdate, PaginatedDeals
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository
from mini_crm.modules.deals.repositories.sqlalchemy import SQLAlchemyDealRepository
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


def get_list_deals_use_case(
    repository: AbstractDealRepository = Depends(get_deal_repository),
) -> ListDealsUseCase:
    return ListDealsUseCase(repository=repository)


def get_create_deal_use_case(
    repository: AbstractDealRepository = Depends(get_deal_repository),
) -> CreateDealUseCase:
    return CreateDealUseCase(repository=repository)


def get_update_deal_use_case(
    repository: AbstractDealRepository = Depends(get_deal_repository),
    activity_repository: AbstractActivityRepository = Depends(get_activity_repository),
) -> UpdateDealUseCase:
    return UpdateDealUseCase(repository=repository, activity_repository=activity_repository)


@router.get("", response_model=PaginatedDeals)
async def list_deals(
    page: int = 1,
    page_size: int = Query(default=50, le=100),
    status_param: list[str] | None = Query(default=None, alias="status"),
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    stage: str | None = None,
    owner_id: int | None = None,
    order_by: str | None = Query(default=None, pattern="^(created_at|amount)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    context: RequestContext = Depends(get_request_context),
    use_case: ListDealsUseCase = Depends(get_list_deals_use_case),
) -> PaginatedDeals:
    # Convert string parameters to enums
    status_enums: list[DealStatus] | None = None
    if status_param:
        status_enums = [DealStatus(s) for s in status_param]

    stage_enum: DealStage | None = None
    if stage:
        stage_enum = DealStage(stage)

    try:
        result = await use_case.execute(
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
        items, meta = result.to_paginated()
        return PaginatedDeals(items=items, meta=meta)
    except DealPermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.post("", response_model=DealResponse, status_code=201)
async def create_deal(
    payload: DealCreate,
    context: RequestContext = Depends(get_request_context),
    use_case: CreateDealUseCase = Depends(get_create_deal_use_case),
) -> DealResponse:
    return await use_case.execute(context, payload)


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: int,
    payload: DealUpdate,
    context: RequestContext = Depends(get_request_context),
    use_case: UpdateDealUseCase = Depends(get_update_deal_use_case),
) -> DealResponse:
    try:
        return await use_case.execute(context, deal_id, payload)
    except DealNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DealPermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except DealValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
