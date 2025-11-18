from __future__ import annotations

from mini_crm.modules.common.application.context import RequestContext
from mini_crm.modules.common.domain.services import PermissionService
from mini_crm.modules.contacts.application.dto import ContactListDTO
from mini_crm.modules.contacts.domain.exceptions import ContactNotFoundError
from mini_crm.modules.contacts.domain.ports import AbstractDealChecker
from mini_crm.modules.contacts.domain.services import ContactDomainService
from mini_crm.modules.contacts.dto.schemas import ContactCreate, ContactResponse
from mini_crm.modules.contacts.repositories.repository import AbstractContactRepository


class ListContactsUseCase:
    """Use case for listing contacts."""

    def __init__(self, repository: AbstractContactRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        context: RequestContext,
        page: int = 1,
        page_size: int = 50,
        search: str | None = None,
        owner_id: int | None = None,
    ) -> ContactListDTO:
        """List contacts with permission checks."""
        if owner_id is not None:
            if not PermissionService.can_filter_by_owner(context.organization.role):
                from mini_crm.modules.common.domain.exceptions import PermissionDeniedError

                raise PermissionDeniedError("Filtering by owner_id is not allowed for member role")

        items, total = await self.repository.list(
            context.organization.organization_id,
            page=page,
            page_size=page_size,
            search=search,
            owner_id=owner_id,
        )
        return ContactListDTO(items=items, total=total, page=page, page_size=page_size)


class CreateContactUseCase:
    """Use case for creating a contact."""

    def __init__(self, repository: AbstractContactRepository) -> None:
        self.repository = repository

    async def execute(self, context: RequestContext, payload: ContactCreate) -> ContactResponse:
        """Create a new contact."""
        contact = await self.repository.create(
            context.organization.organization_id, context.user.id, payload
        )
        return contact


class DeleteContactUseCase:
    """Use case for deleting a contact."""

    def __init__(
        self,
        repository: AbstractContactRepository,
        deal_checker: AbstractDealChecker | None = None,
    ) -> None:
        self.repository = repository
        self.deal_checker = deal_checker

    async def execute(self, context: RequestContext, contact_id: int) -> None:
        """Delete a contact with business rule validation."""
        contact = await self.repository.get_by_id(context.organization.organization_id, contact_id)
        if contact is None:
            raise ContactNotFoundError(contact_id)

        # Check permissions
        if not PermissionService.can_delete_entity(
            context.organization.role, contact.owner_id, context.user.id
        ):
            from mini_crm.modules.common.domain.exceptions import PermissionDeniedError

            raise PermissionDeniedError("You can only delete your own contacts")

        # Check business rules: cannot delete if has deals
        if self.deal_checker:
            has_deals = await self.deal_checker.has_deals_for_contact(contact_id)
            ContactDomainService.validate_deletion(has_deals, contact_id)

        await self.repository.delete(context.organization.organization_id, contact_id)
