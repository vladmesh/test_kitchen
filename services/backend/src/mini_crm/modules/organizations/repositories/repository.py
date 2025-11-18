from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from mini_crm.modules.organizations.dto.schemas import OrganizationDTO
from mini_crm.shared.domain.enums import UserRole

if TYPE_CHECKING:
    from mini_crm.modules.auth.infrastructure.models import OrganizationMember


class AbstractOrganizationRepository(ABC):
    @abstractmethod
    async def list_for_user(self, user_id: int) -> list[OrganizationDTO]:
        raise NotImplementedError

    @abstractmethod
    async def get_membership(self, user_id: int, organization_id: int) -> OrganizationMember | None:
        raise NotImplementedError

    @abstractmethod
    async def add_member(
        self, organization_id: int, user_id: int, role: UserRole
    ) -> OrganizationMember:
        raise NotImplementedError


class InMemoryOrganizationRepository(AbstractOrganizationRepository):
    def __init__(self) -> None:
        self._orgs = [
            OrganizationDTO(id=1, name="Acme Inc"),
            OrganizationDTO(id=2, name="Globex LLC"),
        ]

    async def list_for_user(self, user_id: int) -> list[OrganizationDTO]:  # noqa: ARG002
        return self._orgs

    async def get_membership(self, user_id: int, organization_id: int) -> OrganizationMember | None:  # noqa: ARG002
        return None

    async def add_member(
        self, organization_id: int, user_id: int, role: UserRole
    ) -> OrganizationMember:  # noqa: ARG002
        raise NotImplementedError("InMemoryOrganizationRepository.add_member not implemented")
