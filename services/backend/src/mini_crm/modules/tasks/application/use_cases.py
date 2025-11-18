from __future__ import annotations

from datetime import datetime

from mini_crm.modules.activities.dto.schemas import ActivityCreate
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.common.application.context import RequestContext
from mini_crm.modules.deals.domain.exceptions import DealNotFoundError
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository
from mini_crm.modules.tasks.domain.exceptions import TaskPermissionDeniedError
from mini_crm.modules.tasks.domain.services import TaskDomainService
from mini_crm.modules.tasks.dto.schemas import TaskCreate, TaskResponse
from mini_crm.modules.tasks.repositories.repository import AbstractTaskRepository
from mini_crm.shared.enums import ActivityType, UserRole


class ListTasksUseCase:
    """Use case for listing tasks."""

    def __init__(self, repository: AbstractTaskRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        context: RequestContext,
        deal_id: int | None = None,
        only_open: bool = False,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
    ) -> list[TaskResponse]:
        """List tasks."""
        return await self.repository.list_tasks(
            context.organization.organization_id,
            deal_id=deal_id,
            only_open=only_open,
            due_before=due_before,
            due_after=due_after,
        )


class CreateTaskUseCase:
    """Use case for creating a task."""

    def __init__(
        self,
        repository: AbstractTaskRepository,
        deal_repository: AbstractDealRepository,
        activity_repository: AbstractActivityRepository | None = None,
    ) -> None:
        self.repository = repository
        self.deal_repository = deal_repository
        self.activity_repository = activity_repository

    async def execute(self, context: RequestContext, payload: TaskCreate) -> TaskResponse:
        """Create a new task with business rule validation."""
        # Validate due_date
        TaskDomainService.validate_due_date(payload.due_date)

        # Check deal exists and belongs to organization
        deal = await self.deal_repository.get_by_id(
            context.organization.organization_id,
            payload.deal_id,
        )
        if deal is None:
            raise DealNotFoundError(payload.deal_id)

        deal_org_id = getattr(deal, "organization_id", context.organization.organization_id)
        if deal_org_id != context.organization.organization_id:
            raise TaskPermissionDeniedError("Deal belongs to another organization")

        # Check permissions: member can only create tasks for their own deals
        if context.organization.role == UserRole.MEMBER and deal.owner_id != context.user.id:
            raise TaskPermissionDeniedError("You can only create tasks for your own deals")

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
