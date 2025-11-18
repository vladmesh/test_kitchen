from __future__ import annotations

from mini_crm.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from mini_crm.modules.auth.application.dto import TokenPairDTO
from mini_crm.modules.auth.domain.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from mini_crm.modules.auth.repositories.repository import AbstractAuthRepository


class RegisterUserUseCase:
    """Use case for user registration."""

    def __init__(self, repository: AbstractAuthRepository) -> None:
        self.repository = repository

    async def execute(
        self, email: str, password: str, name: str, organization_name: str
    ) -> TokenPairDTO:
        """Register a new user and create their organization."""
        existing_user = await self.repository.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsError(email)

        hashed_password = get_password_hash(password)
        user = await self.repository.create_user_with_organization(
            email=email,
            password_hash=hashed_password,
            name=name,
            organization_name=organization_name,
        )

        return TokenPairDTO(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )


class LoginUseCase:
    """Use case for user login."""

    def __init__(self, repository: AbstractAuthRepository) -> None:
        self.repository = repository

    async def execute(self, email: str, password: str) -> TokenPairDTO:
        """Authenticate user and return token pair."""
        user = await self.repository.get_by_email(email)
        if not user:
            raise InvalidCredentialsError()

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        return TokenPairDTO(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )
