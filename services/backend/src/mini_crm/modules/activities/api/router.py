from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.activities.application.use_cases import (
    CreateActivityUseCase,
    ListActivitiesUseCase,
)
from mini_crm.modules.activities.domain.exceptions import ActivityValidationError
from mini_crm.modules.activities.dto.schemas import ActivityCreate, ActivityResponse
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.activities.repositories.sqlalchemy import SQLAlchemyActivityRepository
from mini_crm.modules.common.application.context import RequestContext
from mini_crm.modules.deals.domain.exceptions import DealNotFoundError

router = APIRouter(prefix="/deals/{deal_id}/activities", tags=["activities"])


def get_activity_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractActivityRepository:
    return SQLAlchemyActivityRepository(session=session)


def get_list_activities_use_case(
    repository: AbstractActivityRepository = Depends(get_activity_repository),
) -> ListActivitiesUseCase:
    return ListActivitiesUseCase(repository=repository)


def get_create_activity_use_case(
    repository: AbstractActivityRepository = Depends(get_activity_repository),
) -> CreateActivityUseCase:
    return CreateActivityUseCase(repository=repository)


@router.get("", response_model=list[ActivityResponse])
async def list_activities(
    deal_id: int,
    context: RequestContext = Depends(get_request_context),
    use_case: ListActivitiesUseCase = Depends(get_list_activities_use_case),
) -> list[ActivityResponse]:
    return await use_case.execute(context, deal_id)


@router.post("", response_model=ActivityResponse, status_code=201)
async def create_activity(
    deal_id: int,
    payload: ActivityCreate,
    context: RequestContext = Depends(get_request_context),
    use_case: CreateActivityUseCase = Depends(get_create_activity_use_case),
) -> ActivityResponse:
    try:
        return await use_case.execute(context, deal_id, payload)
    except DealNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ActivityValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
