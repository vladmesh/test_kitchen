from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.cache import RedisCache
from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.analytics.application.use_cases import (
    GetDealsFunnelUseCase,
    GetDealsSummaryUseCase,
)
from mini_crm.modules.analytics.dto.schemas import DealsFunnel, DealsSummary
from mini_crm.modules.analytics.repositories.repository import AbstractAnalyticsRepository
from mini_crm.modules.analytics.repositories.sqlalchemy import SQLAlchemyAnalyticsRepository
from mini_crm.modules.common.application.context import RequestContext

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_cache() -> RedisCache:
    """Get Redis cache instance."""
    return RedisCache.get_instance()


def get_analytics_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractAnalyticsRepository:
    return SQLAlchemyAnalyticsRepository(session=session)


def get_deals_summary_use_case(
    repository: AbstractAnalyticsRepository = Depends(get_analytics_repository),
    cache: RedisCache = Depends(get_cache),
) -> GetDealsSummaryUseCase:
    return GetDealsSummaryUseCase(repository=repository, cache=cache)


def get_deals_funnel_use_case(
    repository: AbstractAnalyticsRepository = Depends(get_analytics_repository),
    cache: RedisCache = Depends(get_cache),
) -> GetDealsFunnelUseCase:
    return GetDealsFunnelUseCase(repository=repository, cache=cache)


@router.get("/deals/summary", response_model=DealsSummary)
async def deals_summary(
    context: RequestContext = Depends(get_request_context),
    use_case: GetDealsSummaryUseCase = Depends(get_deals_summary_use_case),
) -> DealsSummary:
    return await use_case.execute(context)


@router.get("/deals/funnel", response_model=DealsFunnel)
async def deals_funnel(
    context: RequestContext = Depends(get_request_context),
    use_case: GetDealsFunnelUseCase = Depends(get_deals_funnel_use_case),
) -> DealsFunnel:
    return await use_case.execute(context)
