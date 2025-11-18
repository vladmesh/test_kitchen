from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session, get_request_user
from mini_crm.modules.auth.domain.exceptions import UserNotFoundError
from mini_crm.modules.auth.repositories.repository import AbstractAuthRepository
from mini_crm.modules.auth.repositories.sqlalchemy import SQLAlchemyAuthRepository
from mini_crm.modules.common.application.context import RequestUser
from mini_crm.modules.common.domain.exceptions import PermissionDeniedError
from mini_crm.modules.organizations.application.use_cases import (
    AddMemberUseCase,
    ListMyOrganizationsUseCase,
)
from mini_crm.modules.organizations.domain.exceptions import MemberAlreadyExistsError
from mini_crm.modules.organizations.dto.schemas import AddMemberRequest, OrganizationListResponse
from mini_crm.modules.organizations.repositories.repository import AbstractOrganizationRepository
from mini_crm.modules.organizations.repositories.sqlalchemy import SQLAlchemyOrganizationRepository

router = APIRouter(prefix="/organizations", tags=["organizations"])


def get_organization_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractOrganizationRepository:
    return SQLAlchemyOrganizationRepository(session=session)


def get_auth_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractAuthRepository:
    return SQLAlchemyAuthRepository(session=session)


def get_list_organizations_use_case(
    repository: AbstractOrganizationRepository = Depends(get_organization_repository),
) -> ListMyOrganizationsUseCase:
    return ListMyOrganizationsUseCase(repository=repository)


def get_add_member_use_case(
    organization_repository: AbstractOrganizationRepository = Depends(get_organization_repository),
    auth_repository: AbstractAuthRepository = Depends(get_auth_repository),
) -> AddMemberUseCase:
    return AddMemberUseCase(
        organization_repository=organization_repository,
        auth_repository=auth_repository,
    )


@router.get("/me", response_model=OrganizationListResponse)
async def list_my_orgs(
    user: RequestUser = Depends(get_request_user),
    use_case: ListMyOrganizationsUseCase = Depends(get_list_organizations_use_case),
) -> OrganizationListResponse:
    result = await use_case.execute(user)
    return OrganizationListResponse(items=result.items)


@router.post("/{organization_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    organization_id: int,
    payload: AddMemberRequest,
    user: RequestUser = Depends(get_request_user),
    use_case: AddMemberUseCase = Depends(get_add_member_use_case),
) -> dict[str, str]:
    try:
        await use_case.execute(
            requester_user_id=user.id,
            organization_id=organization_id,
            target_email=payload.email,
            target_role=payload.role,
        )
        return {"status": "ok"}
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found. They must register first",
        ) from e
    except MemberAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
