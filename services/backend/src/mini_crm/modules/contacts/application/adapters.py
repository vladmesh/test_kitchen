from __future__ import annotations

from mini_crm.modules.contacts.domain.ports import AbstractDealChecker
from mini_crm.modules.deals.repositories.repository import AbstractDealRepository


class DealRepositoryAdapter(AbstractDealChecker):
    """Adapter that wraps AbstractDealRepository to implement AbstractDealChecker port."""

    def __init__(self, deal_repository: AbstractDealRepository) -> None:
        self.deal_repository = deal_repository

    async def has_deals_for_contact(self, contact_id: int) -> bool:
        """Check if contact has any deals by delegating to deal repository."""
        return await self.deal_repository.has_deals_for_contact(contact_id)
