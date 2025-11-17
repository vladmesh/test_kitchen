from __future__ import annotations

from decimal import Decimal

from mini_crm.shared.dto.base import DTO
from mini_crm.shared.dto.pagination import PaginationMeta
from mini_crm.shared.enums import DealStage, DealStatus


class DealCreate(DTO):
    contact_id: int
    title: str
    amount: Decimal
    currency: str = "USD"


class DealUpdate(DTO):
    status: DealStatus | None = None
    stage: DealStage | None = None
    amount: Decimal | None = None


class DealResponse(DTO):
    id: int
    contact_id: int
    owner_id: int | None
    title: str
    amount: Decimal
    currency: str
    status: DealStatus
    stage: DealStage


class PaginatedDeals(DTO):
    items: list[DealResponse]
    meta: PaginationMeta
