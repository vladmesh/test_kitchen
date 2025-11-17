from __future__ import annotations

from abc import ABC, abstractmethod

from mini_crm.modules.analytics.dto.schemas import (
    DealsFunnel,
    DealsSummary,
    StageStats,
    StatusAmount,
    StatusCount,
)


class AbstractAnalyticsRepository(ABC):
    @abstractmethod
    async def deals_summary(self, organization_id: int) -> DealsSummary:
        raise NotImplementedError

    @abstractmethod
    async def deals_funnel(self, organization_id: int) -> DealsFunnel:
        raise NotImplementedError


class InMemoryAnalyticsRepository(AbstractAnalyticsRepository):
    async def deals_summary(self, organization_id: int) -> DealsSummary:  # noqa: ARG002
        return DealsSummary(
            total_deals=0,
            deals_by_status=StatusCount(),
            amounts_by_status=StatusAmount(),
            avg_won_amount=None,
            new_deals_last_30_days=0,
        )

    async def deals_funnel(self, organization_id: int) -> DealsFunnel:  # noqa: ARG002
        return DealsFunnel(
            stages=[
                StageStats(stage="qualification", total=0, by_status=StatusCount()),
            ],
            conversion_rates=[],
        )
