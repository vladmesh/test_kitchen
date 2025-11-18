from __future__ import annotations

from pydantic import EmailStr

from mini_crm.shared.domain.enums import UserRole
from mini_crm.shared.dto.base import DTO


class OrganizationDTO(DTO):
    id: int
    name: str


class OrganizationListResponse(DTO):
    items: list[OrganizationDTO]


class AddMemberRequest(DTO):
    email: EmailStr
    role: UserRole = UserRole.MEMBER
