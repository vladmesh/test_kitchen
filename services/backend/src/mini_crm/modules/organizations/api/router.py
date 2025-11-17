from __future__ import annotations

from fastapi import APIRouter, Depends

from mini_crm.core.dependencies import get_request_context
from mini_crm.modules.common.context import RequestContext
from mini_crm.modules.organizations.dto.schemas import OrganizationListResponse
from mini_crm.modules.organizations.repositories.repository import InMemoryOrganizationRepository
from mini_crm.modules.organizations.services.service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


_organization_repository = InMemoryOrganizationRepository()
_organization_service = OrganizationService(repository=_organization_repository)


def get_organization_service() -> OrganizationService:
    return _organization_service


@router.get("/me", response_model=OrganizationListResponse)
async def list_my_orgs(
    context: RequestContext = Depends(get_request_context),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationListResponse:
    return await service.list_my_organizations(context)
