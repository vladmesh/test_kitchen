from __future__ import annotations

from mini_crm.shared.dto.base import DTO
from mini_crm.shared.enums import ActivityType


class ActivityCreate(DTO):
    type: ActivityType = ActivityType.COMMENT
    payload: dict | None = None


class ActivityResponse(ActivityCreate):
    id: int
    deal_id: int
