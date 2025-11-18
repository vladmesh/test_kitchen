from __future__ import annotations

from mini_crm.shared.domain.exceptions import NotFoundError


class OrganizationNotFoundError(NotFoundError):
    """Raised when an organization is not found."""

    def __init__(self, organization_id: int | None = None) -> None:
        super().__init__("Organization", organization_id)
        self.organization_id = organization_id
