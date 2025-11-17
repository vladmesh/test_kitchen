from __future__ import annotations

from abc import ABC, abstractmethod

from mini_crm.modules.tasks.dto.schemas import TaskCreate, TaskResponse


class AbstractTaskRepository(ABC):
    @abstractmethod
    async def list_for_deal(self, organization_id: int, deal_id: int) -> list[TaskResponse]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, organization_id: int, payload: TaskCreate) -> TaskResponse:
        raise NotImplementedError


class InMemoryTaskRepository(AbstractTaskRepository):
    def __init__(self) -> None:
        self._tasks: list[TaskResponse] = []
        self._counter = 0

    async def list_for_deal(self, organization_id: int, deal_id: int) -> list[TaskResponse]:  # noqa: ARG002
        return [task for task in self._tasks if task.deal_id == deal_id]

    async def create(self, organization_id: int, payload: TaskCreate) -> TaskResponse:  # noqa: ARG002
        self._counter += 1
        task = TaskResponse(id=self._counter, **payload.model_dump())
        self._tasks.append(task)
        return task
