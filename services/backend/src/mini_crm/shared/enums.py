from __future__ import annotations

# Re-export from domain layer for backward compatibility
from mini_crm.shared.domain.enums import (
    ActivityType,
    DealStage,
    DealStatus,
    UserRole,
)

__all__ = ["UserRole", "DealStatus", "DealStage", "ActivityType"]
