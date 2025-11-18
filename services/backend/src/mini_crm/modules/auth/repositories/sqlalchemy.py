from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.auth.models import OrganizationMember, User
from mini_crm.modules.auth.repositories.repository import AbstractAuthRepository, AuthUser
from mini_crm.modules.organizations.models import Organization
from mini_crm.shared.enums import UserRole


class SQLAlchemyAuthRepository(AbstractAuthRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_user_with_organization(
        self, email: str, password_hash: str, name: str, organization_name: str
    ) -> AuthUser:
        user = User(email=email, hashed_password=password_hash, name=name)
        organization = Organization(name=organization_name)
        membership = OrganizationMember(role=UserRole.OWNER, user=user, organization=organization)

        self.session.add_all([user, organization, membership])
        await self.session.flush()

        return AuthUser(id=user.id, email=user.email, hashed_password=user.hashed_password)

    async def get_by_email(self, email: str) -> AuthUser | None:
        stmt = select(User).where(User.email == email).limit(1)
        user = await self.session.scalar(stmt)
        if user is None:
            return None
        return AuthUser(id=user.id, email=user.email, hashed_password=user.hashed_password)

    async def get_by_id(self, user_id: int) -> AuthUser | None:
        stmt = select(User).where(User.id == user_id).limit(1)
        user = await self.session.scalar(stmt)
        if user is None:
            return None
        return AuthUser(id=user.id, email=user.email, hashed_password=user.hashed_password)
