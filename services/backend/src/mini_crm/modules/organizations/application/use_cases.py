from __future__ import annotations

from mini_crm.modules.auth.domain.exceptions import UserNotFoundError
from mini_crm.modules.auth.repositories.repository import AbstractAuthRepository
from mini_crm.modules.common.application.context import RequestUser
from mini_crm.modules.common.domain.exceptions import PermissionDeniedError
from mini_crm.modules.common.domain.services import PermissionService
from mini_crm.modules.organizations.application.dto import OrganizationListDTO
from mini_crm.modules.organizations.domain.exceptions import MemberAlreadyExistsError
from mini_crm.modules.organizations.repositories.repository import AbstractOrganizationRepository
from mini_crm.shared.domain.enums import UserRole


class ListMyOrganizationsUseCase:
    """Use case for listing user's organizations."""

    def __init__(self, repository: AbstractOrganizationRepository) -> None:
        self.repository = repository

    async def execute(self, user: RequestUser) -> OrganizationListDTO:
        """List all organizations for the current user."""
        organizations = await self.repository.list_for_user(user.id)
        return OrganizationListDTO(items=organizations)


class AddMemberUseCase:
    """Use case for adding a member to an organization."""

    def __init__(
        self,
        organization_repository: AbstractOrganizationRepository,
        auth_repository: AbstractAuthRepository,
    ) -> None:
        self.organization_repository = organization_repository
        self.auth_repository = auth_repository

    async def execute(
        self,
        requester_user_id: int,
        organization_id: int,
        target_email: str,
        target_role: UserRole,
    ) -> None:
        """Add a member to an organization."""
        # Check requester permissions
        requester_membership = await self.organization_repository.get_membership(
            requester_user_id, organization_id
        )
        if requester_membership is None:
            raise PermissionDeniedError("You are not a member of this organization")

        requester_role = (
            requester_membership.role
            if isinstance(requester_membership.role, UserRole)
            else UserRole(requester_membership.role)
        )
        PermissionService.ensure_admin_or_owner(requester_role)

        # Find user by email
        target_user = await self.auth_repository.get_by_email(target_email)
        if target_user is None:
            raise UserNotFoundError(email=target_email)

        # Check if user is already a member
        existing_membership = await self.organization_repository.get_membership(
            target_user.id, organization_id
        )
        if existing_membership is not None:
            raise MemberAlreadyExistsError(email=target_email, organization_id=organization_id)

        # Add member
        await self.organization_repository.add_member(organization_id, target_user.id, target_role)
