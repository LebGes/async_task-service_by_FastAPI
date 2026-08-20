import pytest

from app.models.models import (
    TaskPriority,
)
from worker.main import (
    TaskProcessor,
    _priority_from_payload,
)


def test_priority_mapping():
    assert _priority_from_payload(TaskPriority.HIGH.value) == 10
    assert _priority_from_payload(TaskPriority.MEDIUM.value) == 5
    assert _priority_from_payload(TaskPriority.LOW.value) == 1
    assert _priority_from_payload(None) == 5


@pytest.mark.asyncio
async def test_processor_returns_task_id_and_message(pending_task):
    result = await TaskProcessor().process(pending_task)
    assert result['task_id'] == str(pending_task.id)
    assert 'processed successfully' in result['message']
