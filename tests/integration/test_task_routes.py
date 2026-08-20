import uuid
from datetime import (
    datetime,
    timezone,
)
from unittest.mock import (
    AsyncMock,
    patch,
)

from fastapi.testclient import (
    TestClient,
)

from app.main import (
    app,
)
from app.models.models import (
    Task,
    TaskPriority,
    TaskStatus,
)


def make_task(task_id=None, status=TaskStatus.PENDING):
    return Task(
        id=task_id or uuid.uuid4(),
        title='API task',
        description='description',
        priority=TaskPriority.HIGH,
        status=status,
        created_at=datetime.now(timezone.utc),
        attempts=0,
    )


def test_get_task_serializes_repository_result():
    task = make_task()
    with patch('app.services.task_service.TaskRepository.get', new=AsyncMock(return_value=task)):
        with TestClient(app) as client:
            response = client.get(f'/api/v1/tasks/{task.id}')
    assert response.status_code == 200
    assert response.json()['id'] == str(task.id)
    assert response.json()['status'] == 'PENDING'


def test_get_missing_task_returns_404():
    task_id = uuid.uuid4()
    with patch('app.services.task_service.TaskRepository.get', new=AsyncMock(return_value=None)):
        with TestClient(app) as client:
            response = client.get(f'/api/v1/tasks/{task_id}')
    assert response.status_code == 404


def test_status_returns_compact_payload():
    task = make_task()
    with patch('app.services.task_service.TaskRepository.get', new=AsyncMock(return_value=task)):
        with TestClient(app) as client:
            response = client.get(f'/api/v1/tasks/{task.id}/status')
    assert response.status_code == 200
    assert response.json()['status'] == 'PENDING'
    assert 'title' not in response.json()


def test_list_returns_pagination():
    task = make_task()
    with patch('app.api.routes.tasks.TaskRepository.list', new=AsyncMock(return_value=([task], 1))):
        with TestClient(app) as client:
            response = client.get('/api/v1/tasks?status=PENDING&priority=HIGH&limit=10&offset=0')
    assert response.status_code == 200
    body = response.json()
    assert body['total'] == 1
    assert body['limit'] == 10
    assert body['offset'] == 0
    assert len(body['items']) == 1
