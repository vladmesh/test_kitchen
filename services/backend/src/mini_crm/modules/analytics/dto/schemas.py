from __future__ import annotations

from decimal import Decimal

from pydantic import field_serializer

from mini_crm.shared.dto.base import DTO


class StatusCount(DTO):
    new: int = 0
    in_progress: int = 0
    won: int = 0
    lost: int = 0


class StatusAmount(DTO):
    new: Decimal = Decimal("0")
    in_progress: Decimal = Decimal("0")
    won: Decimal = Decimal("0")
    lost: Decimal = Decimal("0")


class DealsSummary(DTO):
    total_deals: int
    deals_by_status: StatusCount
    amounts_by_status: StatusAmount
    avg_won_amount: Decimal | None = None
    new_deals_last_30_days: int = 0

    @field_serializer("avg_won_amount")
    def serialize_avg_won_amount(self, value: Decimal | None) -> str | None:
        if value is None:
            return None
        return f"{value:.2f}"


class StageStats(DTO):
    stage: str
    total: int
    by_status: StatusCount


class ConversionRate(DTO):
    from_stage: str
    to_stage: str
    rate_percent: float


class DealsFunnel(DTO):
    stages: list[StageStats]
    conversion_rates: list[ConversionRate]
