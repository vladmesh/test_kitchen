from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from mini_crm.modules.common.context import OrganizationContext, RequestContext, RequestUser
from mini_crm.shared.enums import UserRole


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
) -> RequestContext:
    if organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="X-Organization-Id header required"
        )

    # TODO: fetch membership/role from DB or cache.
    org_context = OrganizationContext(organization_id=organization_id, role=user.role)
    return RequestContext(user=user, organization=org_context)
