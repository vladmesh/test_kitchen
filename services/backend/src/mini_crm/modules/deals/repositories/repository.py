from __future__ import annotations

from abc import ABC, abstractmethod

from mini_crm.modules.deals.dto.schemas import DealCreate, DealResponse, DealUpdate
from mini_crm.shared.enums import DealStage, DealStatus


class AbstractDealRepository(ABC):
    @abstractmethod
    async def list(
        self, organization_id: int, *, page: int, page_size: int
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
        self, organization_id: int, *, page: int, page_size: int
    ) -> tuple[list[DealResponse], int]:  # noqa: ARG002
        values = list(self._items.values())
        return (values, len(values))

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
