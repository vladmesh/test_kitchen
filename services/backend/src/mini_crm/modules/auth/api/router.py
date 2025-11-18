from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.core.dependencies import get_db_session
from mini_crm.modules.auth.dto.schemas import LoginRequest, RegisterRequest, TokenPair
from mini_crm.modules.auth.repositories.repository import AbstractAuthRepository
from mini_crm.modules.auth.repositories.sqlalchemy import SQLAlchemyAuthRepository
from mini_crm.modules.auth.services.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AbstractAuthRepository:
    return SQLAlchemyAuthRepository(session=session)


def get_auth_service(
    repository: AbstractAuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(repository=repository)


@router.post("/register", response_model=TokenPair)
async def register(
    payload: RegisterRequest, service: AuthService = Depends(get_auth_service)
) -> TokenPair:
    return await service.register(payload)


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest, service: AuthService = Depends(get_auth_service)
) -> TokenPair:
    return await service.login(payload)
