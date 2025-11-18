from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from mini_crm.modules.tasks.dto.schemas import TaskCreate, TaskResponse


class AbstractTaskRepository(ABC):
    @abstractmethod
    async def list_tasks(
        self,
        organization_id: int,
        deal_id: int | None = None,
        only_open: bool = False,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
    ) -> list[TaskResponse]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, organization_id: int, payload: TaskCreate) -> TaskResponse:
        raise NotImplementedError


class InMemoryTaskRepository(AbstractTaskRepository):
    def __init__(self) -> None:
        self._tasks: list[TaskResponse] = []
        self._counter = 0

    async def list_tasks(  # noqa: ARG002
        self,
        organization_id: int,
        deal_id: int | None = None,
        only_open: bool = False,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
    ) -> list[TaskResponse]:
        tasks = self._tasks
        if deal_id is not None:
            tasks = [task for task in tasks if task.deal_id == deal_id]
        if only_open:
            tasks = [task for task in tasks if not task.is_done]
        if due_before is not None:
            tasks = [task for task in tasks if task.due_date and task.due_date <= due_before]
        if due_after is not None:
            tasks = [task for task in tasks if task.due_date and task.due_date >= due_after]
        return tasks

    async def create(self, organization_id: int, payload: TaskCreate) -> TaskResponse:  # noqa: ARG002
        self._counter += 1
        task = TaskResponse(id=self._counter, **payload.model_dump())
        self._tasks.append(task)
        return task
