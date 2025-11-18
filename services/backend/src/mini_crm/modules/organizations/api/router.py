from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_user
from mini_crm.modules.common.application.context import RequestUser
from mini_crm.modules.organizations.application.use_cases import ListMyOrganizationsUseCase
from mini_crm.modules.organizations.dto.schemas import OrganizationListResponse
from mini_crm.modules.organizations.repositories.repository import AbstractOrganizationRepository
from mini_crm.modules.organizations.repositories.sqlalchemy import SQLAlchemyOrganizationRepository

router = APIRouter(prefix="/organizations", tags=["organizations"])


def get_organization_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractOrganizationRepository:
    return SQLAlchemyOrganizationRepository(session=session)


def get_list_organizations_use_case(
    repository: AbstractOrganizationRepository = Depends(get_organization_repository),
) -> ListMyOrganizationsUseCase:
    return ListMyOrganizationsUseCase(repository=repository)


@router.get("/me", response_model=OrganizationListResponse)
async def list_my_orgs(
    user: RequestUser = Depends(get_request_user),
    use_case: ListMyOrganizationsUseCase = Depends(get_list_organizations_use_case),
) -> OrganizationListResponse:
    result = await use_case.execute(user)
    return OrganizationListResponse(items=result.items)
