from __future__ import annotations

from mini_crm.modules.analytics.dto.schemas import DealsFunnel, DealsSummary
from mini_crm.modules.analytics.repositories.repository import (
    AbstractAnalyticsRepository,
    InMemoryAnalyticsRepository,
)
from mini_crm.modules.common.context import RequestContext


class AnalyticsService:
    def __init__(self, repository: AbstractAnalyticsRepository | None = None) -> None:
        self.repository = repository or InMemoryAnalyticsRepository()

    async def deals_summary(self, context: RequestContext) -> DealsSummary:
        return await self.repository.deals_summary(context.organization.organization_id)

    async def deals_funnel(self, context: RequestContext) -> DealsFunnel:
        return await self.repository.deals_funnel(context.organization.organization_id)
