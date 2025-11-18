from __future__ import annotations

from abc import ABC, abstractmethod


class AbstractDealChecker(ABC):
    """Port interface for checking if a contact has active deals."""

    @abstractmethod
    async def has_deals_for_contact(self, contact_id: int) -> bool:
        """Check if contact has any deals."""
        raise NotImplementedError
