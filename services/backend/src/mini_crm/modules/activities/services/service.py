from __future__ import annotations

from fastapi import HTTPException, status

from mini_crm.modules.activities.dto.schemas import ActivityCreate, ActivityResponse
from mini_crm.modules.activities.repositories.repository import (
    AbstractActivityRepository,
    InMemoryActivityRepository,
)
from mini_crm.modules.common.context import RequestContext
from mini_crm.shared.enums import ActivityType


class ActivityService:
    def __init__(self, repository: AbstractActivityRepository | None = None) -> None:
        self.repository = repository or InMemoryActivityRepository()

    async def list_activities(self, context: RequestContext, deal_id: int) -> list[ActivityResponse]:
        return await self.repository.list(context.organization.organization_id, deal_id)

    async def create_activity(self, context: RequestContext, deal_id: int, payload: ActivityCreate) -> ActivityResponse:
        if payload.type != ActivityType.COMMENT and payload.payload is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="payload required for this activity type")
        return await self.repository.create(context.organization.organization_id, deal_id, payload)
