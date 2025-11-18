from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.auth.infrastructure.models import OrganizationMember, User
from mini_crm.modules.auth.repositories.repository import AbstractAuthRepository, AuthUser
from mini_crm.modules.organizations.domain.exceptions import OrganizationAlreadyExistsError
from mini_crm.modules.organizations.infrastructure.models import Organization
from mini_crm.shared.domain.enums import UserRole


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
        try:
            await self.session.flush()
        except IntegrityError as e:
            orig = e.orig
            # Check if error is related to organization name uniqueness
            is_org_name_error = False
            if orig is not None and hasattr(orig, "diag"):
                constraint_name = getattr(orig.diag, "constraint_name", None)
                table_name = getattr(orig.diag, "table_name", None)
                column_name = getattr(orig.diag, "column_name", None)
                if (
                    constraint_name
                    and "organizations" in constraint_name
                    and "name" in constraint_name
                ):
                    is_org_name_error = True
                elif table_name == "organizations" and column_name == "name":
                    is_org_name_error = True
            # Fallback: check error message
            if not is_org_name_error and orig is not None:
                error_str = str(orig).lower()
                if "organizations" in error_str and "name" in error_str and "unique" in error_str:
                    is_org_name_error = True
            if is_org_name_error:
                raise OrganizationAlreadyExistsError(organization_name) from e
            raise

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
