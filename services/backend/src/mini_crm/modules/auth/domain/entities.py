from __future__ import annotations

from datetime import datetime

from mini_crm.shared.domain.base import DomainEntity


class User(DomainEntity):
    """Domain entity representing a user."""

    def __init__(
        self,
        id: int | None = None,
        email: str = "",
        hashed_password: str = "",
        name: str = "",
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(id=id)
        self.email = email
        self.hashed_password = hashed_password
        self.name = name
        self.created_at = created_at or datetime.now()

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, name={self.name})"
