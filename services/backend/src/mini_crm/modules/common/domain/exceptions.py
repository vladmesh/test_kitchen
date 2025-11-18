from __future__ import annotations

from mini_crm.shared.domain.exceptions import PermissionDeniedError as BasePermissionDeniedError


class PermissionDeniedError(BasePermissionDeniedError):
    """Raised when a permission check fails."""

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message)
