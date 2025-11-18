from __future__ import annotations

from mini_crm.modules.activities.domain.exceptions import ActivityValidationError
from mini_crm.modules.activities.dto.schemas import ActivityCreate, ActivityResponse
from mini_crm.modules.activities.repositories.repository import AbstractActivityRepository
from mini_crm.modules.common.application.context import RequestContext
from mini_crm.shared.enums import ActivityType


class ListActivitiesUseCase:
    """Use case for listing activities."""

    def __init__(self, repository: AbstractActivityRepository) -> None:
        self.repository = repository

    async def execute(self, context: RequestContext, deal_id: int) -> list[ActivityResponse]:
        """List activities for a deal."""
        return await self.repository.list(context.organization.organization_id, deal_id)


class CreateActivityUseCase:
    """Use case for creating an activity."""

    def __init__(self, repository: AbstractActivityRepository) -> None:
        self.repository = repository

    async def execute(
        self, context: RequestContext, deal_id: int, payload: ActivityCreate
    ) -> ActivityResponse:
        """Create a new activity with business rule validation."""
        # Only comments can be created via API; other types are created automatically by business logic
        if payload.type != ActivityType.COMMENT:
            raise ActivityValidationError("Only comment activities can be created via API")

        # For comments, use user id as author; for system events, author_id is None
        author_id = context.user.id
        return await self.repository.create(
            context.organization.organization_id, deal_id, payload, author_id=author_id
        )
