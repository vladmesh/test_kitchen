from __future__ import annotations

from mini_crm.shared.dto.base import DTO


class OrganizationDTO(DTO):
    id: int
    name: str


class OrganizationListResponse(DTO):
    items: list[OrganizationDTO]
