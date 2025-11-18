from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session
from mini_crm.modules.auth.application.use_cases import LoginUseCase, RegisterUserUseCase
from mini_crm.modules.auth.domain.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from mini_crm.modules.auth.dto.schemas import LoginRequest, RegisterRequest, TokenPair
from mini_crm.modules.auth.repositories.repository import AbstractAuthRepository
from mini_crm.modules.auth.repositories.sqlalchemy import SQLAlchemyAuthRepository
from mini_crm.modules.organizations.domain.exceptions import OrganizationAlreadyExistsError

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractAuthRepository:
    return SQLAlchemyAuthRepository(session=session)


def get_register_use_case(
    repository: AbstractAuthRepository = Depends(get_auth_repository),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(repository=repository)


def get_login_use_case(
    repository: AbstractAuthRepository = Depends(get_auth_repository),
) -> LoginUseCase:
    return LoginUseCase(repository=repository)


@router.post("/register", response_model=TokenPair)
async def register(
    payload: RegisterRequest, use_case: RegisterUserUseCase = Depends(get_register_use_case)
) -> TokenPair:
    try:
        result = await use_case.execute(
            email=payload.email,
            password=payload.password,
            name=payload.name,
            organization_name=payload.organization_name,
        )
        return TokenPair(access_token=result.access_token, refresh_token=result.refresh_token)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except OrganizationAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest, use_case: LoginUseCase = Depends(get_login_use_case)
) -> TokenPair:
    try:
        result = await use_case.execute(email=payload.email, password=payload.password)
        return TokenPair(access_token=result.access_token, refresh_token=result.refresh_token)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
