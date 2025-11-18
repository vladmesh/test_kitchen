from __future__ import annotations


class DomainError(Exception):
    """Base exception for domain layer."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


# Alias for backward compatibility
DomainException = DomainError


class NotFoundError(DomainException):
    """Raised when an entity is not found."""

    def __init__(self, entity_name: str, entity_id: int | str | None = None) -> None:
        if entity_id is not None:
            message = f"{entity_name} with id {entity_id} not found"
        else:
            message = f"{entity_name} not found"
        super().__init__(message)
        self.entity_name = entity_name
        self.entity_id = entity_id


class ValidationError(DomainException):
    """Raised when domain validation fails."""

    pass


class BusinessRuleViolationError(DomainException):
    """Raised when a business rule is violated."""

    pass


class PermissionDeniedError(DomainException):
    """Raised when a permission check fails."""

    pass
