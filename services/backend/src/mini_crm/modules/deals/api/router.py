from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.activities.repositories.repository import (
    AbstractActivityRepository,
    InMemoryActivityRepository,
)
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.deals.dto.schemas import DealCreate, DealResponse, DealUpdate, PaginatedDeals
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository
from mini_crm.modules.deals.repositories.sqlalchemy import SQLAlchemyDealRepository
from mini_crm.modules.deals.services.service import DealService

router = APIRouter(prefix="/deals", tags=["deals"])


def get_deal_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractDealRepository:
    return SQLAlchemyDealRepository(session=session)


def get_activity_repository() -> AbstractActivityRepository:
    # Temporary: use InMemory until activities module is migrated to PostgreSQL
    return InMemoryActivityRepository()


def get_deal_service(
    repository: AbstractDealRepository = Depends(get_deal_repository),
    activity_repository: AbstractActivityRepository = Depends(get_activity_repository),
) -> DealService:
    return DealService(repository=repository, activity_repository=activity_repository)


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
