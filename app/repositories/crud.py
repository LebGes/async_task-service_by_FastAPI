import uuid

from sqlalchemy import (
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from app.models.models import (
    Task,
    TaskStatus,
    OutboxEvent,
)


class TaskCrud:
    """Репо для работы с задачами."""

    def __init__(self, db_session: AsyncSession):
        """Инициализация.

        :param db_session: Сессия подключения к БД.
        """

        self.session = db_session

    async def create(self, task: Task) -> Task:
        """Создание новой задачи и добавление её в сессию.

        :param task: Новая задача.

        :return: Task: Вернёт задачу.
        """
        self.session.add(task)
        await self.session.flush()

        return task

    async def get(self, task_id: uuid.UUID) -> Task | None:
        """Метод получения задачи по id.

        :param task_id: UUID: id задачи.
        :return: Task | None: Вернуть задачу или ничего
        """

        return await self.session.get(Task, task_id)

    async def list(self, *, status = None, priority = None, limit = 50, offset = 0):
        """Метод получения списка задач.

        :param *
        :param status: Статус задач для фильтрации
        :param priority: Приоритет задач для фильтрации.
        :param limit: Лимит задач.
        :param offset: Смещение.
        """

        filters = []

        if status:
            filters.append(Task.status == status)

        if priority:
            filters.append(Task.priority == priority)

        total = await self.session.scalar(
            select(func.count()).select_from(Task).where(*filters)
        )
        items = (
            await self.session.scalars(
                select(Task)
                .where(*filters)
                .order_by(Task.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()

        return list(items), int(total or 0)

    async def cancel(self, task_id: uuid.UUID) -> Task | None:
        """Отмена задачи.

        :param task_id: UUID: id задачи.

        :return: Task | None: Вернёт задачи или ничего.
        """
        result = await self.session.execute(
            update(Task).where(
                Task.id == task_id,
                Task.status.in_([TaskStatus.NEW, TaskStatus.PENDING]),
            )
            .values(status=TaskStatus.CANCELLED)
            .returning(Task)
        )

        return result.scalar_one_or_none()

    async def claim_for_processing(self, task_id: uuid.UUID) -> bool:
        """Автоматический сбор задач в ожидании для воркера.

        :param task_id:UUID: id задачи.

        :return: bool: Добавлена в воркер или нет.
        """
        result = await self.session.execute(
            update(Task)
            .where(
                Task.id == task_id,
                Task.status == TaskStatus.PENDING,
            )
            .values(
                status=TaskStatus.IN_PROGRESS,
                started_at=func.now(),
                attempts=Task.attempts + 1,
            )
        )

        return result.rowcount == 1

    async def complete(self, task_id: uuid.UUID, result_payload: dict) -> None:
        """Отметка задачи как завершенной.

        :param task_id: UUID: id задачи.
        :param result_payload: dict: результат выполнения задачи.

        """
        await self.session.execute(
            update(Task)
            .where(
                Task.id == task_id,
                Task.status == TaskStatus.IN_PROGRESS
            )
            .values(
                status=TaskStatus.COMPLETED,
                completed_at=func.now(),
                result=result_payload,
                error=None,
            )
        )

    async def fail(self, task_id: uuid.UUID, error_payload: dict) -> None:
        """Отметка о падении задачи.

        :param task_id: UUID: id задачи.
        :param error_payload: dict: описание падения задачи.
        """
        await self.session.execute(
            update(Task)
            .where(
                Task.id == task_id,
                Task.status == TaskStatus.IN_PROGRESS
            )
            .values(
                status=TaskStatus.FAILED,
                completed_at=func.now(),
                error=error_payload,
            )
        )

    async def add_outbox(self, event: OutboxEvent) -> None:
        """Добавление Outbox ивента.

        :param event: OutboxEvent: запись о событии.
        """
        self.session.add(event)
