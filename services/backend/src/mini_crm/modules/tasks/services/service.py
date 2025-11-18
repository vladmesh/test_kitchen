from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status

from mini_crm.modules.activities.dto.schemas import ActivityCreate
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository
from mini_crm.modules.tasks.dto.schemas import TaskCreate, TaskResponse
from mini_crm.modules.tasks.repositories.repository import (
    AbstractTaskRepository,
    InMemoryTaskRepository,
)
from mini_crm.shared.enums import ActivityType, UserRole


class TaskService:
    def __init__(
        self,
        repository: AbstractTaskRepository | None = None,
        activity_repository: AbstractActivityRepository | None = None,
        deal_repository: AbstractDealRepository | None = None,
    ) -> None:
        self.repository = repository or InMemoryTaskRepository()
        self.activity_repository = activity_repository
        self.deal_repository = deal_repository

    async def list_tasks(
        self,
        context: RequestContext,
        deal_id: int | None = None,
        only_open: bool = False,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
    ) -> list[TaskResponse]:
        return await self.repository.list_tasks(
            context.organization.organization_id,
            deal_id=deal_id,
            only_open=only_open,
            due_before=due_before,
            due_after=due_after,
        )

    async def create_task(self, context: RequestContext, payload: TaskCreate) -> TaskResponse:
        if payload.due_date and payload.due_date < datetime.now(tz=UTC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="due_date cannot be in the past"
            )

        if self.deal_repository is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Deal repository is not configured",
            )

        deal = await self.deal_repository.get_by_id(
            context.organization.organization_id,
            payload.deal_id,
        )
        if deal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal not found or does not belong to organization",
            )

        deal_org_id = getattr(deal, "organization_id", context.organization.organization_id)
        if deal_org_id != context.organization.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Deal belongs to another organization",
            )

        if context.organization.role == UserRole.MEMBER and deal.owner_id != context.user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create tasks for your own deals",
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
