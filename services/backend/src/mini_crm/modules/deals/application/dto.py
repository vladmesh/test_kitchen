from __future__ import annotations

from dataclasses import dataclass

from mini_crm.modules.deals.dto.schemas import DealResponse
from mini_crm.shared.dto.pagination import PaginationMeta


@dataclass
class DealListDTO:
    """DTO for deal list."""

    items: list[DealResponse]
    total: int
    page: int
    page_size: int

    def to_paginated(self) -> tuple[list[DealResponse], PaginationMeta]:
        """Convert to paginated response."""
        meta = PaginationMeta(page=self.page, page_size=self.page_size, total=self.total)
        return self.items, meta
