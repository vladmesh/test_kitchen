from __future__ import annotations

from mini_crm.shared.domain.exceptions import DomainException


class InvalidCredentialsError(DomainException):
    """Raised when authentication credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message)


class UserNotFoundError(DomainException):
    """Raised when a user is not found."""

    def __init__(self, email: str | None = None, user_id: int | None = None) -> None:
        if email:
            message = f"User with email {email} not found"
        elif user_id:
            message = f"User with id {user_id} not found"
        else:
            message = "User not found"
        super().__init__(message)
        self.email = email
        self.user_id = user_id


class UserAlreadyExistsError(DomainException):
    """Raised when trying to create a user that already exists."""

    def __init__(self, email: str) -> None:
        message = f"User with email {email} already exists"
        super().__init__(message)
        self.email = email
