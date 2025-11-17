from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from mini_crm.modules.analytics.dto.schemas import DealsFunnel, DealsSummary, FunnelPoint


class AbstractAnalyticsRepository(ABC):
    @abstractmethod
    async def deals_summary(self, organization_id: int) -> DealsSummary:
        raise NotImplementedError

    @abstractmethod
    async def deals_funnel(self, organization_id: int) -> DealsFunnel:
        raise NotImplementedError


class InMemoryAnalyticsRepository(AbstractAnalyticsRepository):
    async def deals_summary(self, organization_id: int) -> DealsSummary:  # noqa: ARG002
        return DealsSummary(total_deals=0, won_deals=0, lost_deals=0, total_amount=Decimal("0"))

    async def deals_funnel(self, organization_id: int) -> DealsFunnel:  # noqa: ARG002
        return DealsFunnel(stages=[FunnelPoint(stage="qualification", value=0)])
