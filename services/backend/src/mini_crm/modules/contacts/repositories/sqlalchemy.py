from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.contacts.dto.schemas import ContactCreate, ContactResponse
from mini_crm.modules.contacts.models import Contact
from mini_crm.modules.contacts.repositories.repository import AbstractContactRepository
from mini_crm.modules.deals.models import Deal


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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )

        # Check if contact has any deals
        deals_stmt = select(func.count()).select_from(Deal).where(Deal.contact_id == contact_id)
        deals_count = await self.session.scalar(deals_stmt)
        if deals_count and deals_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete contact with existing deals",
            )

        await self.session.delete(contact)
        await self.session.flush()
