from fastapi.testclient import (
    TestClient,
)
from app.main import (
    app,
)


def test_create_rejects_empty_title():
    with TestClient(app) as client:
        response = client.post('/api/v1/tasks', json={'title': '', 'priority': 'HIGH'})
    assert response.status_code == 422


def test_create_rejects_invalid_priority():
    with TestClient(app) as client:
        response = client.post('/api/v1/tasks', json={'title': 'demo', 'priority': 'URGENT'})
    assert response.status_code == 422


def test_get_rejects_invalid_uuid():
    with TestClient(app) as client:
        response = client.get('/api/v1/tasks/not-a-uuid')
    assert response.status_code == 422


def test_list_rejects_zero_limit():
    with TestClient(app) as client:
        response = client.get('/api/v1/tasks?limit=0')
    assert response.status_code == 422
