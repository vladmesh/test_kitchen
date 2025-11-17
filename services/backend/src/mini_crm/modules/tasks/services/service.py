from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status

from mini_crm.modules.activities.dto.schemas import ActivityCreate
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.tasks.dto.schemas import TaskCreate, TaskResponse
from mini_crm.modules.tasks.repositories.repository import (
    AbstractTaskRepository,
    InMemoryTaskRepository,
)
from mini_crm.shared.enums import ActivityType


class TaskService:
    def __init__(
        self,
        repository: AbstractTaskRepository | None = None,
        activity_repository: AbstractActivityRepository | None = None,
    ) -> None:
        self.repository = repository or InMemoryTaskRepository()
        self.activity_repository = activity_repository

    async def list_for_deal(self, context: RequestContext, deal_id: int) -> list[TaskResponse]:
        return await self.repository.list_for_deal(context.organization.organization_id, deal_id)

    async def create_task(self, context: RequestContext, payload: TaskCreate) -> TaskResponse:
        if payload.due_date and payload.due_date < datetime.now(tz=UTC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="due_date cannot be in the past"
            )
        task = await self.repository.create(context.organization.organization_id, payload)

        # Create Activity record for task creation
        if self.activity_repository is not None:
            activity_payload = ActivityCreate(
                type=ActivityType.TASK_CREATED,
                payload={"task_id": task.id, "task_title": task.title},
            )
            await self.activity_repository.create(
                context.organization.organization_id,
                payload.deal_id,
                activity_payload,
            )

        return task
