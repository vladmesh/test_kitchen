from __future__ import annotations

from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.organizations.dto.schemas import OrganizationListResponse
from mini_crm.modules.organizations.repositories.repository import (
    AbstractOrganizationRepository,
    InMemoryOrganizationRepository,
)


class OrganizationService:
    def __init__(self, repository: AbstractOrganizationRepository | None = None) -> None:
        self.repository = repository or InMemoryOrganizationRepository()

    async def list_my_organizations(self, context: RequestContext) -> OrganizationListResponse:
        organizations = await self.repository.list_for_user(context.user.id)
        return OrganizationListResponse(items=organizations)
