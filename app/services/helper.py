from app.models.models import (
    TaskStatus,
)


ALLOWED_TRANSITIONS = {
    TaskStatus.NEW: {
        TaskStatus.PENDING,
        TaskStatus.CANCELLED,
    },
    TaskStatus.PENDING: {
        TaskStatus.IN_PROGRESS,
        TaskStatus.CANCELLED,
    },
    TaskStatus.IN_PROGRESS: {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
    },
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.CANCELLED: set(),
}


def can_transition(
    current: TaskStatus,
    new: TaskStatus,
) -> bool:
    return new in ALLOWED_TRANSITIONS[current]