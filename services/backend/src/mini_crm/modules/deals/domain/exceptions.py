from __future__ import annotations

from mini_crm.shared.domain.exceptions import (
    BusinessRuleViolationError,
    NotFoundError,
    PermissionDeniedError,
)


class DealNotFoundError(NotFoundError):
    """Raised when a deal is not found."""

    def __init__(self, deal_id: int | None = None) -> None:
        super().__init__("Deal", deal_id)
        self.deal_id = deal_id


class DealPermissionDeniedError(PermissionDeniedError):
    """Raised when user doesn't have permission to perform action on deal."""

    def __init__(
        self, message: str = "You don't have permission to perform this action on deal"
    ) -> None:
        super().__init__(message)


class DealValidationError(BusinessRuleViolationError):
    """Raised when deal validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
