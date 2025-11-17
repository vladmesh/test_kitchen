from __future__ import annotations

from decimal import Decimal

from mini_crm.shared.dto.base import DTO


class DealsSummary(DTO):
    total_deals: int
    won_deals: int
    lost_deals: int
    total_amount: Decimal


class FunnelPoint(DTO):
    stage: str
    value: int


class DealsFunnel(DTO):
    stages: list[FunnelPoint]
