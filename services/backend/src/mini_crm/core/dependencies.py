from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.db import get_session
from mini_crm.modules.common.context import OrganizationContext, RequestContext, RequestUser
from mini_crm.modules.organizations.repositories.sqlalchemy import (
    SQLAlchemyOrganizationRepository,
)
from mini_crm.shared.enums import UserRole


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with get_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_request_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> RequestUser:
    """Mock current user extraction for the scaffold."""

    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header"
        )

    # TODO: validate JWT once the auth module is fully implemented.
    return RequestUser(id=1, email="owner@example.com", role=UserRole.OWNER)


async def get_request_context(
    user: RequestUser = Depends(get_request_user),
    organization_id: int | None = Header(default=None, alias="X-Organization-Id"),
    session: AsyncSession = Depends(get_db_session),
) -> RequestContext:
    if organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="X-Organization-Id header required"
        )

    repository = SQLAlchemyOrganizationRepository(session)
    membership = await repository.get_membership(user.id, organization_id)

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this organization",
        )

    role = membership.role if isinstance(membership.role, UserRole) else UserRole(membership.role)
    org_context = OrganizationContext(organization_id=organization_id, role=role)
    return RequestContext(user=user, organization=org_context)
