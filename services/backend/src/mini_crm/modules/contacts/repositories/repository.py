from __future__ import annotations

from abc import ABC, abstractmethod

from mini_crm.modules.contacts.dto.schemas import ContactCreate, ContactResponse


class AbstractContactRepository(ABC):
    @abstractmethod
    async def list(
        self, organization_id: int, *, page: int, page_size: int
    ) -> tuple[list[ContactResponse], int]:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self, organization_id: int, owner_id: int, payload: ContactCreate
    ) -> ContactResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, organization_id: int, contact_id: int) -> ContactResponse | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, organization_id: int, contact_id: int) -> None:
        raise NotImplementedError


class InMemoryContactRepository(AbstractContactRepository):
    def __init__(self) -> None:
        self._contacts: list[ContactResponse] = []
        self._counter = 0

    async def list(
        self, organization_id: int, *, page: int, page_size: int
    ) -> tuple[list[ContactResponse], int]:  # noqa: ARG002
        return (self._contacts, len(self._contacts))

    async def create(
        self, organization_id: int, owner_id: int, payload: ContactCreate
    ) -> ContactResponse:  # noqa: ARG002
        self._counter += 1
        contact = ContactResponse(id=self._counter, owner_id=owner_id, **payload.model_dump())
        self._contacts.append(contact)
        return contact

    async def get_by_id(self, organization_id: int, contact_id: int) -> ContactResponse | None:  # noqa: ARG002
        for contact in self._contacts:
            if contact.id == contact_id:
                return contact
        return None

    async def delete(self, organization_id: int, contact_id: int) -> None:  # noqa: ARG002
        self._contacts = [c for c in self._contacts if c.id != contact_id]
