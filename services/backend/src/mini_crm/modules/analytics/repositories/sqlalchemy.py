from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.analytics.dto.schemas import (
    ConversionRate,
    DealsFunnel,
    DealsSummary,
    StageStats,
    StatusAmount,
    StatusCount,
)
from mini_crm.modules.analytics.repositories.repository import AbstractAnalyticsRepository
from mini_crm.modules.deals.models import Deal
from mini_crm.shared.enums import DealStage, DealStatus


class SQLAlchemyAnalyticsRepository(AbstractAnalyticsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def deals_summary(self, organization_id: int) -> DealsSummary:
        # Count deals by status
        count_by_status = select(
            func.count(case((Deal.status == DealStatus.NEW, 1))).label("new"),
            func.count(case((Deal.status == DealStatus.IN_PROGRESS, 1))).label("in_progress"),
            func.count(case((Deal.status == DealStatus.WON, 1))).label("won"),
            func.count(case((Deal.status == DealStatus.LOST, 1))).label("lost"),
        ).where(Deal.organization_id == organization_id)

        count_result = await self.session.execute(count_by_status)
        count_row = count_result.first()
        deals_by_status = StatusCount(
            new=int(count_row.new or 0) if count_row else 0,
            in_progress=int(count_row.in_progress or 0) if count_row else 0,
            won=int(count_row.won or 0) if count_row else 0,
            lost=int(count_row.lost or 0) if count_row else 0,
        )

        # Sum amounts by status
        amount_by_status = select(
            func.coalesce(func.sum(case((Deal.status == DealStatus.NEW, Deal.amount))), 0).label(
                "new"
            ),
            func.coalesce(
                func.sum(case((Deal.status == DealStatus.IN_PROGRESS, Deal.amount))), 0
            ).label("in_progress"),
            func.coalesce(func.sum(case((Deal.status == DealStatus.WON, Deal.amount))), 0).label(
                "won"
            ),
            func.coalesce(func.sum(case((Deal.status == DealStatus.LOST, Deal.amount))), 0).label(
                "lost"
            ),
        ).where(Deal.organization_id == organization_id)

        amount_result = await self.session.execute(amount_by_status)
        amount_row = amount_result.first()
        amounts_by_status = StatusAmount(
            new=Decimal(str(amount_row.new)) if amount_row and amount_row.new else Decimal("0"),
            in_progress=Decimal(str(amount_row.in_progress))
            if amount_row and amount_row.in_progress
            else Decimal("0"),
            won=Decimal(str(amount_row.won)) if amount_row and amount_row.won else Decimal("0"),
            lost=Decimal(str(amount_row.lost)) if amount_row and amount_row.lost else Decimal("0"),
        )

        # Average amount for won deals
        avg_won_stmt = select(func.avg(Deal.amount)).where(
            Deal.organization_id == organization_id, Deal.status == DealStatus.WON
        )
        avg_won_result = await self.session.scalar(avg_won_stmt)
        avg_won_amount = avg_won_result if avg_won_result is not None else None

        # New deals in last 30 days
        thirty_days_ago = datetime.now(tz=UTC) - timedelta(days=30)
        new_deals_stmt = select(func.count(Deal.id)).where(
            Deal.organization_id == organization_id,
            Deal.status == DealStatus.NEW,
            Deal.created_at >= thirty_days_ago,
        )
        new_deals_last_30_days = await self.session.scalar(new_deals_stmt) or 0

        # Total deals count
        total_deals = (
            deals_by_status.new
            + deals_by_status.in_progress
            + deals_by_status.won
            + deals_by_status.lost
        )

        return DealsSummary(
            total_deals=total_deals,
            deals_by_status=deals_by_status,
            amounts_by_status=amounts_by_status,
            avg_won_amount=avg_won_amount,
            new_deals_last_30_days=int(new_deals_last_30_days),
        )

    async def deals_funnel(self, organization_id: int) -> DealsFunnel:
        # Get deals grouped by stage and status
        stage_order = [
            DealStage.QUALIFICATION,
            DealStage.PROPOSAL,
            DealStage.NEGOTIATION,
            DealStage.CLOSED,
        ]

        stages_data: list[StageStats] = []
        stage_counts: dict[str, dict[str, int]] = {}

        # Calculate cumulative counts for each stage
        # Each stage includes all deals that reached this stage or later stages
        for i, stage in enumerate(stage_order):
            # Get all stages from current stage onwards (cumulative)
            stages_to_count = stage_order[i:]

            # Count deals by status for cumulative stages
            count_stmt = select(
                func.count(case((Deal.status == DealStatus.NEW, 1))).label("new"),
                func.count(case((Deal.status == DealStatus.IN_PROGRESS, 1))).label("in_progress"),
                func.count(case((Deal.status == DealStatus.WON, 1))).label("won"),
                func.count(case((Deal.status == DealStatus.LOST, 1))).label("lost"),
            ).where(
                Deal.organization_id == organization_id,
                Deal.stage.in_([s.value for s in stages_to_count]),
            )

            result = await self.session.execute(count_stmt)
            row = result.first()

            status_count = StatusCount(
                new=int(row.new or 0) if row else 0,
                in_progress=int(row.in_progress or 0) if row else 0,
                won=int(row.won or 0) if row else 0,
                lost=int(row.lost or 0) if row else 0,
            )

            total = (
                status_count.new + status_count.in_progress + status_count.won + status_count.lost
            )

            stage_counts[stage.value] = {
                "new": status_count.new,
                "in_progress": status_count.in_progress,
                "won": status_count.won,
                "lost": status_count.lost,
                "total": total,
            }

            stages_data.append(StageStats(stage=stage.value, total=total, by_status=status_count))

        # Calculate conversion rates between stages
        conversion_rates: list[ConversionRate] = []
        for i in range(len(stage_order) - 1):
            from_stage = stage_order[i]
            to_stage = stage_order[i + 1]

            from_total = stage_counts[from_stage.value]["total"]
            to_total = stage_counts[to_stage.value]["total"]

            if from_total > 0:
                rate_percent = (to_total / from_total) * 100.0
            else:
                rate_percent = 0.0

            conversion_rates.append(
                ConversionRate(
                    from_stage=from_stage.value,
                    to_stage=to_stage.value,
                    rate_percent=round(rate_percent, 2),
                )
            )

        return DealsFunnel(stages=stages_data, conversion_rates=conversion_rates)
