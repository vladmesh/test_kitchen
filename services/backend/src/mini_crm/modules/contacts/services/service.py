from __future__ import annotations

from fastapi import HTTPException, status

from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.contacts.dto.schemas import ContactCreate, ContactResponse, PaginatedContacts
from mini_crm.modules.contacts.repositories.repository import (
    AbstractContactRepository,
    InMemoryContactRepository,
)
from mini_crm.shared.dto.pagination import PaginationMeta
from mini_crm.shared.enums import UserRole


class ContactService:
    def __init__(self, repository: AbstractContactRepository | None = None) -> None:
        self.repository = repository or InMemoryContactRepository()

    async def list_contacts(
        self, context: RequestContext, page: int = 1, page_size: int = 50
    ) -> PaginatedContacts:
        items, total = await self.repository.list(
            context.organization.organization_id, page=page, page_size=page_size
        )
        meta = PaginationMeta(page=page, page_size=page_size, total=total)
        return PaginatedContacts(items=items, meta=meta)

    async def create_contact(
        self, context: RequestContext, payload: ContactCreate
    ) -> ContactResponse:
        return await self.repository.create(
            context.organization.organization_id, context.user.id, payload
        )

    async def delete_contact(self, context: RequestContext, contact_id: int) -> None:
        # Check if contact exists and get it for ownership check
        contact = await self.repository.get_by_id(context.organization.organization_id, contact_id)
        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )

        # Check member ownership: member can only delete their own contacts
        if context.organization.role == UserRole.MEMBER:
            if contact.owner_id != context.user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete your own contacts",
                )

        await self.repository.delete(context.organization.organization_id, contact_id)
