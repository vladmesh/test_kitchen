from __future__ import annotations

from pydantic import EmailStr

from mini_crm.shared.dto.base import DTO
from mini_crm.shared.dto.pagination import PaginationMeta


class ContactBase(DTO):
    name: str
    email: EmailStr | None = None
    phone: str | None = None


class ContactCreate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: int
    owner_id: int


class PaginatedContacts(DTO):
    items: list[ContactResponse]
    meta: PaginationMeta
