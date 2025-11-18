from __future__ import annotations

from datetime import UTC, datetime

from mini_crm.modules.tasks.domain.exceptions import TaskValidationError


class TaskDomainService:
    """Domain service for task business rules."""

    @staticmethod
    def validate_due_date(due_date: datetime | None) -> None:
        """Validate that due_date is not in the past."""
        if due_date:
            due_date_date = (
                due_date.astimezone(UTC).date() if due_date.tzinfo is not None else due_date.date()
            )
            today = datetime.now(tz=UTC).date()
            if due_date_date < today:
                raise TaskValidationError("due_date cannot be in the past")
