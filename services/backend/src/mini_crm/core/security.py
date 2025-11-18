from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import jwt

from mini_crm.config.settings import get_settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def _create_token(subject: str | Any, expires_minutes: int, secret: str, algorithm: str) -> str:
    expire = datetime.now(tz=UTC) + timedelta(minutes=expires_minutes)
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
