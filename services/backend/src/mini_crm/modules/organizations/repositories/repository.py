from __future__ import annotations

from abc import ABC, abstractmethod

from mini_crm.modules.organizations.dto.schemas import OrganizationDTO


class AbstractOrganizationRepository(ABC):
    @abstractmethod
    async def list_for_user(self, user_id: int) -> list[OrganizationDTO]:
        raise NotImplementedError


class InMemoryOrganizationRepository(AbstractOrganizationRepository):
    def __init__(self) -> None:
        self._orgs = [
            OrganizationDTO(id=1, name="Acme Inc"),
            OrganizationDTO(id=2, name="Globex LLC"),
        ]

    async def list_for_user(self, user_id: int) -> list[OrganizationDTO]:  # noqa: ARG002
        return self._orgs
