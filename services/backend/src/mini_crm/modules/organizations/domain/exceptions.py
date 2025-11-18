from __future__ import annotations

from mini_crm.shared.domain.exceptions import BusinessRuleViolationError, NotFoundError


class OrganizationNotFoundError(NotFoundError):
    """Raised when an organization is not found."""

    def __init__(self, organization_id: int | None = None) -> None:
        super().__init__("Organization", organization_id)
        self.organization_id = organization_id


class MemberAlreadyExistsError(BusinessRuleViolationError):
    """Raised when trying to add a member that already exists in the organization."""

    def __init__(self, email: str, organization_id: int) -> None:
        message = f"User with email {email} is already a member of this organization"
        super().__init__(message)
        self.email = email
        self.organization_id = organization_id
