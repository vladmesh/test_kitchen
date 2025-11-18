from __future__ import annotations

from decimal import Decimal

from mini_crm.modules.deals.domain.exceptions import DealValidationError
from mini_crm.shared.enums import DealStage, UserRole


class DealDomainService:
    """Domain service for deal business rules."""

    @staticmethod
    def validate_won_deal_amount(amount: Decimal | None) -> None:
        """Validate that won deal has positive amount."""
        if amount is not None and amount <= 0:
            raise DealValidationError("Amount must be positive for won deals")

    @staticmethod
    def _get_stage_order(stage: DealStage) -> int:
        """Get order of stage in pipeline."""
        stage_order = [
            DealStage.QUALIFICATION,
            DealStage.PROPOSAL,
            DealStage.NEGOTIATION,
            DealStage.CLOSED,
        ]
        return stage_order.index(stage)

    @staticmethod
    def is_stage_rollback(old_stage: DealStage, new_stage: DealStage) -> bool:
        """Check if stage change is a rollback."""
        return DealDomainService._get_stage_order(new_stage) < DealDomainService._get_stage_order(
            old_stage
        )

    @staticmethod
    def can_rollback_stage(role: UserRole) -> bool:
        """Check if user role can rollback deal stage."""
        return role in {UserRole.ADMIN, UserRole.OWNER}

    @staticmethod
    def validate_stage_rollback(old_stage: DealStage, new_stage: DealStage, role: UserRole) -> None:
        """Validate stage rollback permission."""
        if DealDomainService.is_stage_rollback(old_stage, new_stage):
            if not DealDomainService.can_rollback_stage(role):
                raise DealValidationError("Stage rollback is not allowed for your role")
