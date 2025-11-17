from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.activities.dto.schemas import ActivityCreate, ActivityResponse
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.activities.repositories.sqlalchemy import SQLAlchemyActivityRepository
from mini_crm.modules.activities.services.service import ActivityService
from mini_crm.modules.common.context import RequestContext

router = APIRouter(prefix="/deals/{deal_id}/activities", tags=["activities"])


def get_activity_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractActivityRepository:
    return SQLAlchemyActivityRepository(session=session)


def get_activity_service(
    repository: AbstractActivityRepository = Depends(get_activity_repository),
) -> ActivityService:
    return ActivityService(repository=repository)


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
