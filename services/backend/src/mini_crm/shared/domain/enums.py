from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"


class DealStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


class DealStage(str, Enum):
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED = "closed"


class ActivityType(str, Enum):
    COMMENT = "comment"
    STATUS_CHANGED = "status_changed"
    STAGE_CHANGED = "stage_changed"
    TASK_CREATED = "task_created"
    SYSTEM = "system"
