from __future__ import annotations

from dataclasses import dataclass

from mini_crm.shared.enums import UserRole


@dataclass
class RequestUser:
    id: int
    email: str


@dataclass
class OrganizationContext:
    organization_id: int
    role: UserRole


@dataclass
class RequestContext:
    user: RequestUser
    organization: OrganizationContext
