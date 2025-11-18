from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_context
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.organizations.dto.schemas import OrganizationListResponse
from mini_crm.modules.organizations.repositories.repository import AbstractOrganizationRepository
from mini_crm.modules.organizations.repositories.sqlalchemy import SQLAlchemyOrganizationRepository
from mini_crm.modules.organizations.services.service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


def get_organization_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractOrganizationRepository:
    return SQLAlchemyOrganizationRepository(session=session)


def get_organization_service(
    repository: AbstractOrganizationRepository = Depends(get_organization_repository),
) -> OrganizationService:
    return OrganizationService(repository=repository)


@router.get("/me", response_model=OrganizationListResponse)
async def list_my_orgs(
    context: RequestContext = Depends(get_request_context),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationListResponse:
    return await service.list_my_organizations(context)
