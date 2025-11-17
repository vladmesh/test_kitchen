from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AuthUser:
    id: int
    email: str
    hashed_password: str


class AbstractAuthRepository(ABC):
    @abstractmethod
    async def create_user_with_organization(self, email: str, password_hash: str, name: str, organization_name: str) -> AuthUser:  # noqa: D401
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> AuthUser | None:
        raise NotImplementedError


class InMemoryAuthRepository(AbstractAuthRepository):
    def __init__(self) -> None:
        self._users: dict[str, AuthUser] = {}
        self._counter = 0

    async def create_user_with_organization(self, email: str, password_hash: str, name: str, organization_name: str) -> AuthUser:  # noqa: ARG002
        self._counter += 1
        user = AuthUser(id=self._counter, email=email, hashed_password=password_hash)
        self._users[email] = user
        return user

    async def get_by_email(self, email: str) -> AuthUser | None:
        return self._users.get(email)
