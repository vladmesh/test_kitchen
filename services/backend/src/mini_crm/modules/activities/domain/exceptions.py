from __future__ import annotations

from mini_crm.shared.domain.exceptions import BusinessRuleViolationError


class ActivityValidationError(BusinessRuleViolationError):
    """Raised when activity validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
