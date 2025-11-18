from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.db import get_session
from mini_crm.core.security import InvalidTokenError, decode_access_token
from mini_crm.modules.auth.repositories.sqlalchemy import SQLAlchemyAuthRepository
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
    session: AsyncSession = Depends(get_db_session),
) -> RequestUser:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header"
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header"
        )

    try:
        payload = decode_access_token(token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token"
        ) from exc

    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        ) from exc

    repository = SQLAlchemyAuthRepository(session)
    auth_user = await repository.get_by_id(user_id)
    if auth_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return RequestUser(id=auth_user.id, email=auth_user.email, role=UserRole.OWNER)


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
