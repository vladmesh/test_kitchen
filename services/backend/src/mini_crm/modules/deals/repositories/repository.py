from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
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

    @abstractmethod
    async def get_by_id(self, organization_id: int, deal_id: int) -> DealResponse | None:
        raise NotImplementedError

    @abstractmethod
    async def has_deals_for_contact(self, contact_id: int) -> bool:
        """Check if contact has any deals."""
        raise NotImplementedError


class InMemoryDealRepository(AbstractDealRepository):
    def __init__(self) -> None:
        self._items: dict[int, DealResponse] = {}
        self._counter = 0
        self._organization_ids: dict[int, int] = {}

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
        now = datetime.now(tz=UTC)
        deal = DealResponse(
            id=self._counter,
            organization_id=organization_id,
            contact_id=payload.contact_id,
            owner_id=owner_id,
            title=payload.title,
            amount=payload.amount,
            currency=payload.currency,
            status=DealStatus.NEW,
            stage=DealStage.QUALIFICATION,
            created_at=now,
            updated_at=now,
        )
        self._items[self._counter] = deal
        self._organization_ids[self._counter] = organization_id
        return deal

    async def update(self, organization_id: int, deal_id: int, payload: DealUpdate) -> DealResponse:  # noqa: ARG002
        deal = self._items[deal_id]
        update_data = payload.model_dump(exclude_none=True)
        update_data["updated_at"] = datetime.now(tz=UTC)
        updated = deal.model_copy(update=update_data)
        self._items[deal_id] = updated
        return updated

    async def get_by_id(self, organization_id: int, deal_id: int) -> DealResponse | None:
        deal = self._items.get(deal_id)
        if deal is None:
            return None
        if self._organization_ids.get(deal_id) != organization_id:
            return None
        return deal

    async def has_deals_for_contact(self, contact_id: int) -> bool:  # noqa: ARG002
        """Check if contact has any deals."""
        return any(deal.contact_id == contact_id for deal in self._items.values())
