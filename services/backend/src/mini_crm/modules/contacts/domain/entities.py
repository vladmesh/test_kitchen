from __future__ import annotations

from datetime import datetime

from mini_crm.shared.domain.base import DomainEntity


class Contact(DomainEntity):
    """Domain entity representing a contact."""

    def __init__(
        self,
        id: int | None = None,
        organization_id: int = 0,
        owner_id: int = 0,
        name: str = "",
        email: str | None = None,
        phone: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(id=id)
        self.organization_id = organization_id
        self.owner_id = owner_id
        self.name = name
        self.email = email
        self.phone = phone
        self.created_at = created_at or datetime.now()

    def __repr__(self) -> str:
        return f"Contact(id={self.id}, name={self.name}, organization_id={self.organization_id})"
