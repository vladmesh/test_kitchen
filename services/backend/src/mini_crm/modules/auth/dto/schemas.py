from __future__ import annotations

from pydantic import EmailStr

from mini_crm.shared.dto.base import DTO


class RegisterRequest(DTO):
    email: EmailStr
    password: str
    name: str
    organization_name: str


class LoginRequest(DTO):
    email: EmailStr
    password: str


class TokenPair(DTO):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
