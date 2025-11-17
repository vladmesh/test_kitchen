from __future__ import annotations

from mini_crm.shared.dto.base import DTO


class PaginationMeta(DTO):
    page: int
    page_size: int
    total: int


class PaginatedResponse(DTO):
    items: list[object]
    meta: PaginationMeta
