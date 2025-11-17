from __future__ import annotations

from fastapi import APIRouter, Depends

from mini_crm.core.dependencies import get_request_context
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.tasks.dto.schemas import TaskCreate, TaskResponse
from mini_crm.modules.tasks.repositories.repository import InMemoryTaskRepository
from mini_crm.modules.tasks.services.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


_task_repository = InMemoryTaskRepository()
_task_service = TaskService(repository=_task_repository)


def get_task_service() -> TaskService:
    return _task_service


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
