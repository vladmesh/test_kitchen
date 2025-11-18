from __future__ import annotations

from mini_crm.shared.domain.exceptions import BusinessRuleViolationError, PermissionDeniedError


class TaskValidationError(BusinessRuleViolationError):
    """Raised when task validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class TaskPermissionDeniedError(PermissionDeniedError):
    """Raised when user doesn't have permission to perform action on task."""

    def __init__(
        self, message: str = "You don't have permission to perform this action on task"
    ) -> None:
        super().__init__(message)
