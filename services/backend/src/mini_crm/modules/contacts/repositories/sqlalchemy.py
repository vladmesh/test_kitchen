from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.contacts.dto.schemas import ContactCreate, ContactResponse
from mini_crm.modules.contacts.models import Contact
from mini_crm.modules.contacts.repositories.repository import AbstractContactRepository


class SQLAlchemyContactRepository(AbstractContactRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self, organization_id: int, *, page: int, page_size: int
    ) -> tuple[list[ContactResponse], int]:
        offset = max(page - 1, 0) * page_size
        stmt = (
            select(Contact)
            .where(Contact.organization_id == organization_id)
            .order_by(Contact.id)
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.scalars(stmt)
        contacts = result.all()

        count_stmt = (
            select(func.count())
            .select_from(Contact)
            .where(Contact.organization_id == organization_id)
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
