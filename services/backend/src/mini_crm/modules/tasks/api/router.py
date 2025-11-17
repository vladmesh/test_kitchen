from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.activities.repositories.sqlalchemy import SQLAlchemyActivityRepository
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.tasks.dto.schemas import TaskCreate, TaskResponse
from mini_crm.modules.tasks.repositories.repository import AbstractTaskRepository
from mini_crm.modules.tasks.repositories.sqlalchemy import SQLAlchemyTaskRepository
from mini_crm.modules.tasks.services.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractTaskRepository:
    return SQLAlchemyTaskRepository(session=session)


def get_activity_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractActivityRepository:
    return SQLAlchemyActivityRepository(session=session)


def get_task_service(
    repository: AbstractTaskRepository = Depends(get_task_repository),
    activity_repository: AbstractActivityRepository = Depends(get_activity_repository),
) -> TaskService:
    return TaskService(repository=repository, activity_repository=activity_repository)


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    deal_id: int,
    context: RequestContext = Depends(get_request_context),
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    return await service.list_for_deal(context, deal_id)


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    payload: TaskCreate,
    context: RequestContext = Depends(get_request_context),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return await service.create_task(context, payload)
