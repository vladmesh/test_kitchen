from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.auth.infrastructure.models import OrganizationMember
from mini_crm.modules.organizations.dto.schemas import OrganizationDTO
from mini_crm.modules.organizations.infrastructure.models import Organization
from mini_crm.modules.organizations.repositories.repository import AbstractOrganizationRepository


class SQLAlchemyOrganizationRepository(AbstractOrganizationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: int) -> list[OrganizationDTO]:
        stmt = (
            select(Organization)
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(OrganizationMember.user_id == user_id)
            .distinct()
        )
        result = await self.session.scalars(stmt)
        organizations = result.all()
        return [OrganizationDTO(id=org.id, name=org.name) for org in organizations]

    async def get_membership(self, user_id: int, organization_id: int) -> OrganizationMember | None:
        stmt = select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == organization_id,
        )
        result = await self.session.scalar(stmt)
        return result
