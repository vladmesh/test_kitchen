from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status

from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.tasks.dto.schemas import TaskCreate, TaskResponse
from mini_crm.modules.tasks.repositories.repository import (
    AbstractTaskRepository,
    InMemoryTaskRepository,
)


class TaskService:
    def __init__(self, repository: AbstractTaskRepository | None = None) -> None:
        self.repository = repository or InMemoryTaskRepository()

    async def list_for_deal(self, context: RequestContext, deal_id: int) -> list[TaskResponse]:
        return await self.repository.list_for_deal(context.organization.organization_id, deal_id)

    async def create_task(self, context: RequestContext, payload: TaskCreate) -> TaskResponse:
        if payload.due_date and payload.due_date < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="due_date cannot be in the past"
            )
        return await self.repository.create(context.organization.organization_id, payload)
