from __future__ import annotations

from mini_crm.modules.common.domain.exceptions import PermissionDeniedError
from mini_crm.shared.domain.enums import UserRole

ROLE_ORDER = [UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN, UserRole.OWNER]


class PermissionService:
    """Domain service for permission checks."""

    @staticmethod
    def ensure_min_role(current_role: UserRole, minimum: UserRole) -> None:
        """Ensure current role meets minimum requirement."""
        current_index = ROLE_ORDER.index(current_role)
        minimum_index = ROLE_ORDER.index(minimum)
        if current_index < minimum_index:
            raise PermissionDeniedError(
                f"Role {current_role.value} does not meet minimum requirement {minimum.value}"
            )

    @staticmethod
    def ensure_owner(current_role: UserRole) -> None:
        """Ensure current role is owner."""
        PermissionService.ensure_min_role(current_role, UserRole.OWNER)

    @staticmethod
    def ensure_admin_or_owner(current_role: UserRole) -> None:
        """Ensure current role is admin or owner."""
        if current_role not in {UserRole.ADMIN, UserRole.OWNER}:
            raise PermissionDeniedError("Admin or owner privileges required")

    @staticmethod
    def can_filter_by_owner(current_role: UserRole) -> bool:
        """Check if current role can filter by owner_id."""
        return current_role != UserRole.MEMBER

    @staticmethod
    def can_update_entity(
        current_role: UserRole, entity_owner_id: int, current_user_id: int
    ) -> bool:
        """Check if current role can update entity."""
        if current_role == UserRole.MEMBER:
            return entity_owner_id == current_user_id
        return True

    @staticmethod
    def can_delete_entity(
        current_role: UserRole, entity_owner_id: int, current_user_id: int
    ) -> bool:
        """Check if current role can delete entity."""
        if current_role == UserRole.MEMBER:
            return entity_owner_id == current_user_id
        return True

    @staticmethod
    def can_rollback_stage(current_role: UserRole) -> bool:
        """Check if current role can rollback deal stage."""
        return current_role in {UserRole.ADMIN, UserRole.OWNER}
