from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.contacts.dto.schemas import ContactCreate, ContactResponse, PaginatedContacts
from mini_crm.modules.contacts.repositories.repository import AbstractContactRepository
from mini_crm.modules.contacts.repositories.sqlalchemy import SQLAlchemyContactRepository
from mini_crm.modules.contacts.services.service import ContactService

router = APIRouter(prefix="/contacts", tags=["contacts"])


def get_contact_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractContactRepository:
    return SQLAlchemyContactRepository(session=session)


def get_contact_service(
    repository: AbstractContactRepository = Depends(get_contact_repository),
) -> ContactService:
    return ContactService(repository=repository)


@router.get("", response_model=PaginatedContacts)
async def list_contacts(
    page: int = 1,
    page_size: int = 50,
    search: str | None = None,
    owner_id: int | None = None,
    context: RequestContext = Depends(get_request_context),
    service: ContactService = Depends(get_contact_service),
) -> PaginatedContacts:
    return await service.list_contacts(
        context,
        page=page,
        page_size=page_size,
        search=search,
        owner_id=owner_id,
    )


@router.post("", response_model=ContactResponse, status_code=201)
async def create_contact(
    payload: ContactCreate,
    context: RequestContext = Depends(get_request_context),
    service: ContactService = Depends(get_contact_service),
) -> ContactResponse:
    return await service.create_contact(context, payload)


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    context: RequestContext = Depends(get_request_context),
    service: ContactService = Depends(get_contact_service),
) -> Response:
    await service.delete_contact(context, contact_id)
    return Response(status_code=204)
