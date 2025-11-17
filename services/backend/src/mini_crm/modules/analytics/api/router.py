from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.analytics.dto.schemas import DealsFunnel, DealsSummary
from mini_crm.modules.analytics.repositories.repository import AbstractAnalyticsRepository
from mini_crm.modules.analytics.repositories.sqlalchemy import SQLAlchemyAnalyticsRepository
from mini_crm.modules.analytics.services.service import AnalyticsService
from mini_crm.modules.common.context import RequestContext

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractAnalyticsRepository:
    return SQLAlchemyAnalyticsRepository(session=session)


def get_analytics_service(
    repository: AbstractAnalyticsRepository = Depends(get_analytics_repository),
) -> AnalyticsService:
    return AnalyticsService(repository=repository)


@router.get("/deals/summary", response_model=DealsSummary)
async def deals_summary(
    context: RequestContext = Depends(get_request_context),
    service: AnalyticsService = Depends(get_analytics_service),
) -> DealsSummary:
    return await service.deals_summary(context)


@router.get("/deals/funnel", response_model=DealsFunnel)
async def deals_funnel(
    context: RequestContext = Depends(get_request_context),
    service: AnalyticsService = Depends(get_analytics_service),
) -> DealsFunnel:
    return await service.deals_funnel(context)
