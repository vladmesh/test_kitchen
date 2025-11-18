from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DomainEntity:
    """Base class for domain entities."""

    id: int | None = None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, DomainEntity):
            return False
        if self.id is None or other.id is None:
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        if self.id is None:
            return hash(id(self))
        return hash(self.id)
