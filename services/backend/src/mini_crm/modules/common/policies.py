from __future__ import annotations

from fastapi import HTTPException, status

from mini_crm.modules.common.application.context import RequestContext
from mini_crm.modules.common.domain.exceptions import PermissionDeniedError
from mini_crm.modules.common.domain.services import PermissionService
from mini_crm.shared.domain.enums import UserRole


def ensure_min_role(context: RequestContext, minimum: UserRole) -> None:
    """Check minimum role requirement, raise HTTPException if failed."""
    try:
        PermissionService.ensure_min_role(context.organization.role, minimum)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


def ensure_owner(context: RequestContext) -> None:
    """Check owner role, raise HTTPException if failed."""
    try:
        PermissionService.ensure_owner(context.organization.role)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


def ensure_admin_or_owner(context: RequestContext) -> None:
    """Check admin or owner role, raise HTTPException if failed."""
    try:
        PermissionService.ensure_admin_or_owner(context.organization.role)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
