from __future__ import annotations

from datetime import datetime

from mini_crm.shared.domain.base import DomainEntity


class Organization(DomainEntity):
    """Domain entity representing an organization."""

    def __init__(
        self,
        id: int | None = None,
        name: str = "",
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(id=id)
        self.name = name
        self.created_at = created_at or datetime.now()

    def __repr__(self) -> str:
        return f"Organization(id={self.id}, name={self.name})"
