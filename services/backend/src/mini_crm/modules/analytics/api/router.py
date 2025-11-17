from __future__ import annotations

from fastapi import APIRouter, Depends

from mini_crm.core.dependencies import get_request_context
from mini_crm.modules.analytics.dto.schemas import DealsFunnel, DealsSummary
from mini_crm.modules.analytics.repositories.repository import InMemoryAnalyticsRepository
from mini_crm.modules.analytics.services.service import AnalyticsService
from mini_crm.modules.common.context import RequestContext

router = APIRouter(prefix="/analytics", tags=["analytics"])


_analytics_repository = InMemoryAnalyticsRepository()
_analytics_service = AnalyticsService(repository=_analytics_repository)


def get_analytics_service() -> AnalyticsService:
    return _analytics_service


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
