from unittest.mock import (
    AsyncMock,
)

import pytest

from app.models.models import (
    TaskPriority,
    TaskStatus,
)
from app.repositories.crud import (
    TaskCrud,
)


@pytest.mark.asyncio
async def test_create_adds_and_flushes(mock_session, pending_task):
    repo = TaskCrud(mock_session)
    assert await repo.create(pending_task) is pending_task
    mock_session.add.assert_called_once_with(pending_task)
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_delegates_to_session(mock_session, task_id):
    mock_session.get = AsyncMock(return_value=None)
    repo = TaskCrud(mock_session)
    assert await repo.get(task_id) is None
    mock_session.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_returns_items_and_count(mock_session):
    mock_session.scalar = AsyncMock(return_value=3)
    result = Magic = type('Result', (), {'all': lambda self: ['a', 'b']})()
    mock_session.scalars = AsyncMock(return_value=result)
    repo = TaskCrud(mock_session)
    items, total = await repo.list(status=TaskStatus.PENDING, priority=TaskPriority.HIGH, limit=10, offset=5)
    assert items == ['a', 'b']
    assert total == 3


@pytest.mark.asyncio
async def test_claim_is_true_for_one_updated_row(mock_session):
    result = type('Result', (), {'rowcount': 1})()
    mock_session.execute = AsyncMock(return_value=result)
    assert await TaskCrud(mock_session).claim_for_processing('id') is True


@pytest.mark.asyncio
async def test_claim_is_false_for_zero_updated_rows(mock_session):
    result = type('Result', (), {'rowcount': 0})()
    mock_session.execute = AsyncMock(return_value=result)
    assert await TaskCrud(mock_session).claim_for_processing('id') is False


@pytest.mark.asyncio
async def test_complete_executes_update(mock_session):
    await TaskCrud(mock_session).complete('id', {'ok': True})
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_fail_executes_update(mock_session):
    await TaskCrud(mock_session).fail('id', {'message': 'boom'})
    mock_session.execute.assert_awaited_once()
