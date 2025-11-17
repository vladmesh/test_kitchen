from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from mini_crm.modules.deals.dto.schemas import DealCreate, DealResponse, DealUpdate
from mini_crm.shared.enums import DealStage, DealStatus


class AbstractDealRepository(ABC):
    @abstractmethod
    async def list(
        self,
        organization_id: int,
        *,
        page: int,
        page_size: int,
        status: list[DealStatus] | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        stage: DealStage | None = None,
        owner_id: int | None = None,
        order_by: str | None = None,
        order: str = "asc",
    ) -> tuple[list[DealResponse], int]:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self, organization_id: int, owner_id: int, payload: DealCreate
    ) -> DealResponse:
        raise NotImplementedError

    @abstractmethod
    async def update(self, organization_id: int, deal_id: int, payload: DealUpdate) -> DealResponse:
        raise NotImplementedError


class InMemoryDealRepository(AbstractDealRepository):
    def __init__(self) -> None:
        self._items: dict[int, DealResponse] = {}
        self._counter = 0

    async def list(
        self,
        organization_id: int,  # noqa: ARG002
        *,
        page: int,
        page_size: int,
        status: list[DealStatus] | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        stage: DealStage | None = None,
        owner_id: int | None = None,
        order_by: str | None = None,
        order: str = "asc",
    ) -> tuple[list[DealResponse], int]:
        values = list(self._items.values())

        # Apply filters
        if status:
            values = [v for v in values if v.status in status]
        if min_amount is not None:
            values = [v for v in values if v.amount >= min_amount]
        if max_amount is not None:
            values = [v for v in values if v.amount <= max_amount]
        if stage is not None:
            values = [v for v in values if v.stage == stage]
        if owner_id is not None:
            values = [v for v in values if v.owner_id == owner_id]

        # Apply sorting
        if order_by == "created_at":
            values.sort(key=lambda x: getattr(x, "created_at", 0), reverse=(order == "desc"))
        elif order_by == "amount":
            values.sort(key=lambda x: x.amount, reverse=(order == "desc"))

        total = len(values)

        # Apply pagination
        offset = max(page - 1, 0) * page_size
        paginated_values = values[offset : offset + page_size]

        return (paginated_values, total)

    async def create(
        self, organization_id: int, owner_id: int, payload: DealCreate
    ) -> DealResponse:  # noqa: ARG002
        self._counter += 1
        deal = DealResponse(
            id=self._counter,
            contact_id=payload.contact_id,
            owner_id=owner_id,
            title=payload.title,
            amount=payload.amount,
            currency=payload.currency,
            status=DealStatus.NEW,
            stage=DealStage.QUALIFICATION,
        )
        self._items[self._counter] = deal
        return deal

    async def update(self, organization_id: int, deal_id: int, payload: DealUpdate) -> DealResponse:  # noqa: ARG002
        deal = self._items[deal_id]
        updated = deal.model_copy(update=payload.model_dump(exclude_none=True))
        self._items[deal_id] = updated
        return updated
