from __future__ import annotations

from abc import ABC, abstractmethod

from mini_crm.modules.activities.dto.schemas import ActivityCreate, ActivityResponse


class AbstractActivityRepository(ABC):
    @abstractmethod
    async def list(self, organization_id: int, deal_id: int) -> list[ActivityResponse]:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self, organization_id: int, deal_id: int, payload: ActivityCreate
    ) -> ActivityResponse:
        raise NotImplementedError


class InMemoryActivityRepository(AbstractActivityRepository):
    def __init__(self) -> None:
        self._activities: list[ActivityResponse] = []
        self._counter = 0

    async def list(self, organization_id: int, deal_id: int) -> list[ActivityResponse]:  # noqa: ARG002
        return [activity for activity in self._activities if activity.deal_id == deal_id]

    async def create(
        self, organization_id: int, deal_id: int, payload: ActivityCreate
    ) -> ActivityResponse:  # noqa: ARG002
        self._counter += 1
        activity = ActivityResponse(id=self._counter, deal_id=deal_id, **payload.model_dump())
        self._activities.append(activity)
        return activity
