from unittest.mock import (
    AsyncMock,
)

import pytest
from fastapi import (
    HTTPException,
)

from app.models.models import (
    TaskPriority,
    TaskStatus,
)
from app.schemas.schemas import (
    TaskCreate,
)
from app.services.task_service import (
    TaskService,
)


@pytest.mark.asyncio
async def test_create_creates_pending_task_and_outbox(mock_session):
    service = TaskService(mock_session)
    service.repo.create = AsyncMock()
    service.repo.add_outbox = AsyncMock()

    task = await service.create(TaskCreate(title="demo", priority=TaskPriority.HIGH))

    assert task.status == TaskStatus.PENDING
    assert task.priority == TaskPriority.HIGH
    service.repo.create.assert_awaited_once()
    service.repo.add_outbox.assert_awaited_once()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_raises_404_for_missing_task(mock_session):
    service = TaskService(mock_session)
    service.repo.get = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await service.get(__import__('uuid').uuid4())

    assert exc.value.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [
    TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED
])
async def test_cancel_rejects_non_cancellable_states(mock_session, pending_task, status):
    pending_task.status = status
    service = TaskService(mock_session)
    service.repo.get = AsyncMock(return_value=pending_task)
    service.repo.cancel = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await service.cancel(pending_task.id)

    assert exc.value.status_code == 409
    service.repo.cancel.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_detects_concurrent_state_change(mock_session, pending_task):
    service = TaskService(mock_session)
    service.repo.get = AsyncMock(return_value=pending_task)
    service.repo.cancel = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await service.cancel(pending_task.id)

    assert exc.value.status_code == 409
