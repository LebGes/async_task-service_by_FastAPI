from app.models.models import (
    TaskPriority,
    TaskStatus,
)


def test_status_values():
    assert {x.value for x in TaskStatus} == {
        "NEW", "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "CANCELLED"
    }


def test_priority_values():
    assert {x.value for x in TaskPriority} == {"LOW", "MEDIUM", "HIGH"}
