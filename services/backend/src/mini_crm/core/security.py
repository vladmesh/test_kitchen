from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from mini_crm.config.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _create_token(subject: str | Any, expires_minutes: int, secret: str, algorithm: str) -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, secret, algorithm=algorithm)


def create_access_token(subject: str | Any) -> str:
    settings = get_settings()
    return _create_token(
        subject=subject,
        expires_minutes=settings.access_token_expire_minutes,
        secret=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(subject: str | Any) -> str:
    settings = get_settings()
    return _create_token(
        subject=subject,
        expires_minutes=settings.refresh_token_expire_minutes,
        secret=settings.jwt_refresh_secret_key,
        algorithm=settings.jwt_algorithm,
    )
