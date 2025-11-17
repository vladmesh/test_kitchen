from __future__ import annotations

from fastapi import HTTPException, status

from mini_crm.modules.common.context import RequestContext
from mini_crm.shared.enums import UserRole


ROLE_ORDER = [UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN, UserRole.OWNER]


def ensure_min_role(context: RequestContext, minimum: UserRole) -> None:
    if ROLE_ORDER.index(context.organization.role) < ROLE_ORDER.index(minimum):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def ensure_owner(context: RequestContext) -> None:
    ensure_min_role(context, UserRole.OWNER)


def ensure_admin_or_owner(context: RequestContext) -> None:
    if context.organization.role not in {UserRole.ADMIN, UserRole.OWNER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
