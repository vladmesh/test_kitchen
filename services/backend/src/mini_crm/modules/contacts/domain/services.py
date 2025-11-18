from __future__ import annotations


class ContactDomainService:
    """Domain service for contact business rules."""

    @staticmethod
    def can_delete_contact(has_deals: bool) -> bool:
        """Check if contact can be deleted based on business rules."""
        return not has_deals

    @staticmethod
    def validate_deletion(has_deals: bool, contact_id: int) -> None:
        """Validate that contact can be deleted."""
        if has_deals:
            from mini_crm.modules.contacts.domain.exceptions import ContactHasActiveDealsError

            raise ContactHasActiveDealsError(contact_id)
