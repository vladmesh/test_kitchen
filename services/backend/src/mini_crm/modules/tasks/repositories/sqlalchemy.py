from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mini_crm.modules.deals.models import Deal
from mini_crm.modules.tasks.dto.schemas import TaskCreate, TaskResponse
from mini_crm.modules.tasks.models import Task
from mini_crm.modules.tasks.repositories.repository import AbstractTaskRepository


class SQLAlchemyTaskRepository(AbstractTaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_tasks(
        self,
        organization_id: int,
        deal_id: int | None = None,
        only_open: bool = False,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
    ) -> list[TaskResponse]:
        # Join with Deal to ensure tasks belong to organization
        stmt = (
            select(Task)
            .join(Deal, Task.deal_id == Deal.id)
            .where(Deal.organization_id == organization_id)
            .order_by(Task.created_at.desc())
        )

        if deal_id is not None:
            stmt = stmt.where(Task.deal_id == deal_id)
        if only_open:
            stmt = stmt.where(Task.is_done.is_(False))
        if due_before is not None:
            stmt = stmt.where(Task.due_date.is_not(None), Task.due_date <= due_before)
        if due_after is not None:
            stmt = stmt.where(Task.due_date.is_not(None), Task.due_date >= due_after)

        result = await self.session.scalars(stmt)
        tasks = result.all()

        return [TaskResponse.model_validate(task) for task in tasks]

    async def create(self, organization_id: int, payload: TaskCreate) -> TaskResponse:
        # Check if deal exists and belongs to organization
        deal_stmt = select(Deal).where(
            Deal.id == payload.deal_id,
            Deal.organization_id == organization_id,
        )
        deal = await self.session.scalar(deal_stmt)
        if deal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal not found or does not belong to organization",
            )

        task = Task(
            deal_id=payload.deal_id,
            title=payload.title,
            description=payload.description,
            due_date=payload.due_date,
            is_done=False,
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return TaskResponse.model_validate(task)
