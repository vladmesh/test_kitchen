from __future__ import annotations

from fastapi import APIRouter, Depends

from mini_crm.modules.auth.dto.schemas import LoginRequest, RegisterRequest, TokenPair
from mini_crm.modules.auth.repositories.repository import InMemoryAuthRepository
from mini_crm.modules.auth.services.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


_auth_repository = InMemoryAuthRepository()
_auth_service = AuthService(repository=_auth_repository)


def get_auth_service() -> AuthService:
    return _auth_service


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
