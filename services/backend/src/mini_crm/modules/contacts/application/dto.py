from __future__ import annotations

from dataclasses import dataclass

from mini_crm.modules.contacts.dto.schemas import ContactResponse
from mini_crm.shared.dto.pagination import PaginationMeta


@dataclass
class ContactListDTO:
    """DTO for contact list."""

    items: list[ContactResponse]
    total: int
    page: int
    page_size: int

    def to_paginated(self) -> tuple[list[ContactResponse], PaginationMeta]:
        """Convert to paginated response."""
        from mini_crm.shared.dto.pagination import PaginationMeta

        meta = PaginationMeta(page=self.page, page_size=self.page_size, total=self.total)
        return self.items, meta
