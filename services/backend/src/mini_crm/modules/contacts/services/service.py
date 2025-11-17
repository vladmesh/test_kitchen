from __future__ import annotations

from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.contacts.dto.schemas import ContactCreate, ContactResponse, PaginatedContacts
from mini_crm.modules.contacts.repositories.repository import (
    AbstractContactRepository,
    InMemoryContactRepository,
)
from mini_crm.shared.dto.pagination import PaginationMeta


class ContactService:
    def __init__(self, repository: AbstractContactRepository | None = None) -> None:
        self.repository = repository or InMemoryContactRepository()

    async def list_contacts(self, context: RequestContext, page: int = 1, page_size: int = 50) -> PaginatedContacts:
        items, total = await self.repository.list(context.organization.organization_id, page=page, page_size=page_size)
        meta = PaginationMeta(page=page, page_size=page_size, total=total)
        return PaginatedContacts(items=items, meta=meta)

    async def create_contact(self, context: RequestContext, payload: ContactCreate) -> ContactResponse:
        return await self.repository.create(context.organization.organization_id, context.user.id, payload)
