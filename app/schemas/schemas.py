import uuid

from datetime import (
    datetime,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models.models import (
    TaskPriority,
    TaskStatus,
)

class TaskCreate(BaseModel):
    """Схема создания задачи."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM

class TaskResponse(BaseModel):
    """Схема ответа с данными задачи."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    result: dict | None
    error: dict | None
    attempts: int

class TaskStatusResponse(BaseModel):
    """Краткий ответ со статусом задачи."""

    id: uuid.UUID
    status: TaskStatus
    started_at: datetime | None
    completed_at: datetime | None
    error: dict | None

class TaskListResponse(BaseModel):
    """Ответ со списком задач и пагинацией."""

    items: list[TaskResponse]
    total: int
    limit: int
    offset: int
