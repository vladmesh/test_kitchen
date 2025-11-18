from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.contacts.domain.exceptions import ContactNotFoundError
from mini_crm.modules.contacts.dto.schemas import ContactCreate, ContactResponse
from mini_crm.modules.contacts.models import Contact
from mini_crm.modules.contacts.repositories.repository import AbstractContactRepository


class SQLAlchemyContactRepository(AbstractContactRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        organization_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        owner_id: int | None = None,
    ) -> tuple[list[ContactResponse], int]:
        offset = max(page - 1, 0) * page_size
        stmt = select(Contact).where(Contact.organization_id == organization_id)

        if owner_id is not None:
            stmt = stmt.where(Contact.owner_id == owner_id)

        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Contact.name.ilike(pattern), Contact.email.ilike(pattern)))

        stmt = stmt.order_by(Contact.id).offset(offset).limit(page_size)
        result = await self.session.scalars(stmt)
        contacts = result.all()

        count_stmt = (
            select(func.count())
            .select_from(Contact)
            .where(Contact.organization_id == organization_id)
        )
        if owner_id is not None:
            count_stmt = count_stmt.where(Contact.owner_id == owner_id)
        if search:
            pattern = f"%{search}%"
            count_stmt = count_stmt.where(
                or_(Contact.name.ilike(pattern), Contact.email.ilike(pattern))
            )
        total = await self.session.scalar(count_stmt)

        items = [ContactResponse.model_validate(contact) for contact in contacts]
        return items, int(total or 0)

    async def create(
        self, organization_id: int, owner_id: int, payload: ContactCreate
    ) -> ContactResponse:
        contact = Contact(
            organization_id=organization_id,
            owner_id=owner_id,
            created_at=datetime.now(tz=UTC),
            **payload.model_dump(),
        )
        self.session.add(contact)
        await self.session.flush()
        await self.session.refresh(contact)
        return ContactResponse.model_validate(contact)

    async def get_by_id(self, organization_id: int, contact_id: int) -> ContactResponse | None:
        stmt = select(Contact).where(
            Contact.id == contact_id,
            Contact.organization_id == organization_id,
        )
        contact = await self.session.scalar(stmt)
        if contact is None:
            return None
        return ContactResponse.model_validate(contact)

    async def delete(self, organization_id: int, contact_id: int) -> None:
        # Check if contact exists and belongs to organization
        contact_stmt = select(Contact).where(
            Contact.id == contact_id,
            Contact.organization_id == organization_id,
        )
        contact = await self.session.scalar(contact_stmt)
        if contact is None:
            raise ContactNotFoundError(contact_id)

        await self.session.delete(contact)
        await self.session.flush()
