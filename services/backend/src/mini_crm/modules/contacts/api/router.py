from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.common.application.context import RequestContext
from mini_crm.modules.common.domain.exceptions import PermissionDeniedError
from mini_crm.modules.contacts.application.use_cases import (
    CreateContactUseCase,
    DeleteContactUseCase,
    ListContactsUseCase,
)
from mini_crm.modules.contacts.domain.exceptions import (
    ContactHasActiveDealsError,
    ContactNotFoundError,
)
from mini_crm.modules.contacts.dto.schemas import ContactCreate, ContactResponse, PaginatedContacts
from mini_crm.modules.contacts.repositories.repository import AbstractContactRepository
from mini_crm.modules.contacts.repositories.sqlalchemy import SQLAlchemyContactRepository
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository
from mini_crm.modules.deals.repositories.sqlalchemy import SQLAlchemyDealRepository

router = APIRouter(prefix="/contacts", tags=["contacts"])


def get_contact_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractContactRepository:
    return SQLAlchemyContactRepository(session=session)


def get_deal_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractDealRepository:
    return SQLAlchemyDealRepository(session=session)


def get_list_contacts_use_case(
    repository: AbstractContactRepository = Depends(get_contact_repository),
) -> ListContactsUseCase:
    return ListContactsUseCase(repository=repository)


def get_create_contact_use_case(
    repository: AbstractContactRepository = Depends(get_contact_repository),
) -> CreateContactUseCase:
    return CreateContactUseCase(repository=repository)


def get_delete_contact_use_case(
    repository: AbstractContactRepository = Depends(get_contact_repository),
    deal_repository: AbstractDealRepository = Depends(get_deal_repository),
) -> DeleteContactUseCase:
    return DeleteContactUseCase(repository=repository, deal_repository=deal_repository)


@router.get("", response_model=PaginatedContacts)
async def list_contacts(
    page: int = 1,
    page_size: int = 50,
    search: str | None = None,
    owner_id: int | None = None,
    context: RequestContext = Depends(get_request_context),
    use_case: ListContactsUseCase = Depends(get_list_contacts_use_case),
) -> PaginatedContacts:
    try:
        result = await use_case.execute(
            context,
            page=page,
            page_size=page_size,
            search=search,
            owner_id=owner_id,
        )
        items, meta = result.to_paginated()
        return PaginatedContacts(items=items, meta=meta)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.post("", response_model=ContactResponse, status_code=201)
async def create_contact(
    payload: ContactCreate,
    context: RequestContext = Depends(get_request_context),
    use_case: CreateContactUseCase = Depends(get_create_contact_use_case),
) -> ContactResponse:
    return await use_case.execute(context, payload)


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    context: RequestContext = Depends(get_request_context),
    use_case: DeleteContactUseCase = Depends(get_delete_contact_use_case),
) -> Response:
    try:
        await use_case.execute(context, contact_id)
        return Response(status_code=204)
    except ContactNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ContactHasActiveDealsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
