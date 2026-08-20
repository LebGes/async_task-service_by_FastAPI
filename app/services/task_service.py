import uuid

from fastapi import (
    HTTPException,
    status,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models.models import (
    OutboxEvent,
    Task,
    TaskStatus,
)
from app.repositories.crud import (
    TaskCrud,
)
from app.schemas.schemas import (
    TaskCreate,
)


class TaskService:
    """Служебный класс для соблюдения бизнес-логики."""

    def __init__(self, session: AsyncSession):
        """Инициализация.

        :param session: AsyncSession: Сессия подключения к БД.
        """

        self.crud = TaskCrud(session)
        self.session = session

    async def create(self, data: TaskCreate) -> Task:
        """Создание задачи и добавление её в Outbox.

        :param data: TaskCreate: Исходные данные для создания задачи.

        :return: Task: Созданная задача.
        """

        task = Task(
            title=data.title,
            description=data.description,
            priority=data.priority,
            status=TaskStatus.PENDING,
        )
        await self.crud.create(task)
        await self.crud.add_outbox(
            OutboxEvent(
                task_id=task.id,
                event_type='TASK_CREATED',
                payload={
                    'task_id': str(task.id),
                    'priority': data.priority.value,
                },
            )
        )
        await self.session.commit()
        await self.session.refresh(task)

        return task

    async def get(self, task_id: uuid.UUID) -> Task:
        """Получение задачи по id.

        :param task_id: uuid.UUID: id задачи.

        :return: Task: Полученная задача.
        """

        task = await self.crud.get(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Task not found',
            )

        return task

    async def cancel(self, task_id: uuid.UUID) -> Task:
        """Отмена задачи по id.

        :param task_id: uuid.UUID: id задачи.

        :return: Task: Отменённая задача.
        """

        task = await self.crud.get(task_id)

        if not task:
            raise HTTPException(
                status_code=404,
                detail='Task not found',
            )

        if task.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.IN_PROGRESS,
        }:
            raise HTTPException(
                status_code=409,
                detail=f'Task cannot be cancelled from {task.status.value}',
            )

        cancelled = await self.crud.cancel(task_id)

        if not cancelled:
            raise HTTPException(
                status_code=409,
                detail='Task state changed; cancellation rejected',
            )

        await self.session.commit()
        await self.session.refresh(cancelled)

        return cancelled
