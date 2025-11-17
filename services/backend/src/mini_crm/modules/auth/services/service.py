from __future__ import annotations

from fastapi import HTTPException, status

from mini_crm.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from mini_crm.modules.auth.dto.schemas import LoginRequest, RegisterRequest, TokenPair
from mini_crm.modules.auth.repositories.repository import AbstractAuthRepository, InMemoryAuthRepository


class AuthService:
    def __init__(self, repository: AbstractAuthRepository | None = None) -> None:
        self.repository = repository or InMemoryAuthRepository()

    async def register(self, payload: RegisterRequest) -> TokenPair:
        hashed_password = get_password_hash(payload.password)
        user = await self.repository.create_user_with_organization(
            email=payload.email,
            password_hash=hashed_password,
            name=payload.name,
            organization_name=payload.organization_name,
        )
        return TokenPair(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))

    async def login(self, payload: LoginRequest) -> TokenPair:
        user = await self.repository.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return TokenPair(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))
