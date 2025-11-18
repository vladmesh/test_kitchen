from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.activities.repositories.sqlalchemy import SQLAlchemyActivityRepository
from mini_crm.modules.common.application.context import RequestContext
from mini_crm.modules.deals.domain.exceptions import DealNotFoundError
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository
from mini_crm.modules.deals.repositories.sqlalchemy import SQLAlchemyDealRepository
from mini_crm.modules.tasks.application.use_cases import CreateTaskUseCase, ListTasksUseCase
from mini_crm.modules.tasks.domain.exceptions import (
    TaskPermissionDeniedError,
    TaskValidationError,
)
from mini_crm.modules.tasks.dto.schemas import TaskCreate, TaskResponse
from mini_crm.modules.tasks.repositories.repository import AbstractTaskRepository
from mini_crm.modules.tasks.repositories.sqlalchemy import SQLAlchemyTaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractTaskRepository:
    return SQLAlchemyTaskRepository(session=session)


def get_activity_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractActivityRepository:
    return SQLAlchemyActivityRepository(session=session)


def get_deal_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractDealRepository:
    return SQLAlchemyDealRepository(session=session)


def get_list_tasks_use_case(
    repository: AbstractTaskRepository = Depends(get_task_repository),
) -> ListTasksUseCase:
    return ListTasksUseCase(repository=repository)


def get_create_task_use_case(
    repository: AbstractTaskRepository = Depends(get_task_repository),
    deal_repository: AbstractDealRepository = Depends(get_deal_repository),
    activity_repository: AbstractActivityRepository = Depends(get_activity_repository),
) -> CreateTaskUseCase:
    return CreateTaskUseCase(
        repository=repository,
        deal_repository=deal_repository,
        activity_repository=activity_repository,
    )


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    deal_id: int | None = Query(default=None),
    only_open: bool = Query(default=False),
    due_before: datetime | None = Query(default=None),
    due_after: datetime | None = Query(default=None),
    context: RequestContext = Depends(get_request_context),
    use_case: ListTasksUseCase = Depends(get_list_tasks_use_case),
) -> list[TaskResponse]:
    return await use_case.execute(
        context,
        deal_id=deal_id,
        only_open=only_open,
        due_before=due_before,
        due_after=due_after,
    )


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    payload: TaskCreate,
    context: RequestContext = Depends(get_request_context),
    use_case: CreateTaskUseCase = Depends(get_create_task_use_case),
) -> TaskResponse:
    try:
        return await use_case.execute(context, payload)
    except DealNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except TaskPermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except TaskValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
