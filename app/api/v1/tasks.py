import uuid

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.db.db_session import (
    get_session,
)
from app.models.models import (
    TaskPriority,
    TaskStatus,
)
from app.repositories.crud import (
    TaskCrud,
)
from app.schemas.schemas import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskStatusResponse,
)
from app.services.task_service import (
    TaskService,
)


router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.post('', response_model=TaskResponse, status_code=201)
async def create_task(
        data: TaskCreate,
        session: AsyncSession = Depends(get_session)
):
    """Создание задачи из приходящих данных.

    :param data: TaskCreate: Исходные данные.
    :param session: AsyncSession: Сессия в которой идёт обработка данных.

    :return: Возвращает созданную задачу.
    """

    return await TaskService(session).create(data)


@router.get('', response_model=TaskListResponse)
async def list_tasks(
    status: TaskStatus | None = Query(None),
    priority: TaskPriority | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Запрашивает список задач с примененными фильтрами.

    :param status: TaskStatus | None: Статус задачи.
    :param priority: TaskPriority | None: Приоритет задачи.
    :param limit: int: лимит задач.
    :param offset: int: Смещение.
    :param session: AsyncSession: Сессия в которой идёт обработка данных.

    :return: ответ сервера со списком.
    """

    items, total = await TaskCrud(session).list(
        status=status, priority=priority, limit=limit, offset=offset
    )

    return TaskListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get('/{task_id}', response_model=TaskResponse)
async def get_task(
        task_id: uuid.UUID,
        session: AsyncSession = Depends(get_session)
):
    """Получение задачи по её id.

    :param task_id: uuid.UUID: id задачи.
    :param session: AsyncSession: Сессия в которой идёт обработка данных.

    :return: Возвращает запрашиваемую задачу.
    """

    return await TaskService(session).get(task_id)


@router.delete('/{task_id}', response_model=TaskResponse)
async def cancel_task(
        task_id: uuid.UUID,
        session: AsyncSession = Depends(get_session)
):
    """Отмена задачи по её id.

    :param task_id: uuid.UUID: id задачи.
    :param session: AsyncSession: Сессия в которой идёт обработка данных.

    :return: Возвращает отмененную задачу или ничего.
    """

    return await TaskService(session).cancel(task_id)


@router.get('/{task_id}/status', response_model=TaskStatusResponse)
async def get_task_status(
        task_id: uuid.UUID,
        session: AsyncSession = Depends(get_session)
):
    """Получает статус задачи по её id.

    :param task_id: uuid.UUID: id задачи.
    :param session: AsyncSession: Сессия в которой идёт обработка данных.

    :return: Возвращает краткую информацию со статусом задачи.
    """

    task = await TaskService(session).get(task_id)

    return TaskStatusResponse(
        id=task.id,
        status=task.status,
        started_at=task.started_at,
        completed_at=task.completed_at,
        error=task.error,
    )
