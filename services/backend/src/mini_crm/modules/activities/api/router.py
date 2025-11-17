from __future__ import annotations

from fastapi import APIRouter, Depends

from mini_crm.core.dependencies import get_request_context
from mini_crm.modules.activities.dto.schemas import ActivityCreate, ActivityResponse
from mini_crm.modules.activities.repositories.repository import InMemoryActivityRepository
from mini_crm.modules.activities.services.service import ActivityService
from mini_crm.modules.common.context import RequestContext

router = APIRouter(prefix="/deals/{deal_id}/activities", tags=["activities"])


_activity_repository = InMemoryActivityRepository()
_activity_service = ActivityService(repository=_activity_repository)


def get_activity_service() -> ActivityService:
    return _activity_service


@router.get("", response_model=list[ActivityResponse])
async def list_activities(
    deal_id: int,
    context: RequestContext = Depends(get_request_context),
    service: ActivityService = Depends(get_activity_service),
) -> list[ActivityResponse]:
    return await service.list_activities(context, deal_id)


@router.post("", response_model=ActivityResponse, status_code=201)
async def create_activity(
    deal_id: int,
    payload: ActivityCreate,
    context: RequestContext = Depends(get_request_context),
    service: ActivityService = Depends(get_activity_service),
) -> ActivityResponse:
    return await service.create_activity(context, deal_id, payload)
