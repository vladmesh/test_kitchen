from __future__ import annotations

from datetime import datetime

from mini_crm.shared.dto.base import DTO


class TaskCreate(DTO):
    deal_id: int
    title: str
    description: str | None = None
    due_date: datetime | None = None


class TaskResponse(TaskCreate):
    id: int
    is_done: bool = False
