from __future__ import annotations

from mini_crm.shared.domain.exceptions import BusinessRuleViolationError, NotFoundError


class ContactNotFoundError(NotFoundError):
    """Raised when a contact is not found."""

    def __init__(self, contact_id: int | None = None) -> None:
        super().__init__("Contact", contact_id)
        self.contact_id = contact_id


class ContactHasActiveDealsError(BusinessRuleViolationError):
    """Raised when trying to delete a contact that has active deals."""

    def __init__(self, contact_id: int) -> None:
        message = f"Cannot delete contact {contact_id} with existing deals"
        super().__init__(message)
        self.contact_id = contact_id
