from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """Base class for domain events."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: int | None = None
    aggregate_type: str = ""

    def __post_init__(self) -> None:
        if not self.aggregate_type:
            self.aggregate_type = self.__class__.__name__.replace("Event", "").lower()
