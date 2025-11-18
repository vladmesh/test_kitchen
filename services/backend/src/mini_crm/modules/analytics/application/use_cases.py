from __future__ import annotations

from mini_crm.modules.analytics.dto.schemas import DealsFunnel, DealsSummary
from mini_crm.modules.analytics.repositories.repository import AbstractAnalyticsRepository
from mini_crm.modules.common.application.context import RequestContext


class GetDealsSummaryUseCase:
    """Use case for getting deals summary."""

    def __init__(self, repository: AbstractAnalyticsRepository) -> None:
        self.repository = repository

    async def execute(self, context: RequestContext) -> DealsSummary:
        """Get deals summary for the organization."""
        return await self.repository.deals_summary(context.organization.organization_id)


class GetDealsFunnelUseCase:
    """Use case for getting deals funnel."""

    def __init__(self, repository: AbstractAnalyticsRepository) -> None:
        self.repository = repository

    async def execute(self, context: RequestContext) -> DealsFunnel:
        """Get deals funnel for the organization."""
        return await self.repository.deals_funnel(context.organization.organization_id)
