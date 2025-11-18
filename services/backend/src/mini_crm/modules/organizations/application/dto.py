from __future__ import annotations

from dataclasses import dataclass

from mini_crm.modules.organizations.dto.schemas import OrganizationDTO


@dataclass
class OrganizationListDTO:
    """DTO for organization list."""

    items: list[OrganizationDTO]
