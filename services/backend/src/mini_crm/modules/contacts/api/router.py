from __future__ import annotations

from fastapi import APIRouter, Depends

from mini_crm.core.dependencies import get_request_context
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.contacts.dto.schemas import ContactCreate, ContactResponse, PaginatedContacts
from mini_crm.modules.contacts.repositories.repository import InMemoryContactRepository
from mini_crm.modules.contacts.services.service import ContactService

router = APIRouter(prefix="/contacts", tags=["contacts"])


_contacts_repository = InMemoryContactRepository()
_contacts_service = ContactService(repository=_contacts_repository)


def get_contact_service() -> ContactService:
    return _contacts_service


@router.get("", response_model=PaginatedContacts)
async def list_contacts(
    page: int = 1,
    page_size: int = 50,
    context: RequestContext = Depends(get_request_context),
    service: ContactService = Depends(get_contact_service),
) -> PaginatedContacts:
    return await service.list_contacts(context, page=page, page_size=page_size)


@router.post("", response_model=ContactResponse, status_code=201)
async def create_contact(
    payload: ContactCreate,
    context: RequestContext = Depends(get_request_context),
    service: ContactService = Depends(get_contact_service),
) -> ContactResponse:
    return await service.create_contact(context, payload)
