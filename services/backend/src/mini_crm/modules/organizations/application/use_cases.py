from __future__ import annotations

from mini_crm.modules.common.application.context import RequestUser
from mini_crm.modules.organizations.application.dto import OrganizationListDTO
from mini_crm.modules.organizations.repositories.repository import AbstractOrganizationRepository


class ListMyOrganizationsUseCase:
    """Use case for listing user's organizations."""

    def __init__(self, repository: AbstractOrganizationRepository) -> None:
        self.repository = repository

    async def execute(self, user: RequestUser) -> OrganizationListDTO:
        """List all organizations for the current user."""
        organizations = await self.repository.list_for_user(user.id)
        return OrganizationListDTO(items=organizations)
