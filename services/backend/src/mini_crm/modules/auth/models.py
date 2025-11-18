from __future__ import annotations

# Re-export from infrastructure layer for backward compatibility
from mini_crm.modules.auth.infrastructure.models import OrganizationMember, User

__all__ = ["User", "OrganizationMember"]
