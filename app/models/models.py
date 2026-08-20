import enum
import uuid

from datetime import (
    datetime,
)

from sqlalchemy import (
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.db_base import (
    Base,
)


class TaskStatus(str, enum.Enum):
    """Класс статуса задачи."""

    NEW = 'NEW'
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'


class TaskPriority(str, enum.Enum):
    """Класс приоритета задачи."""

    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'


class Task(Base):
    """Модель задачи."""

    __tablename__ = 'tasks'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,)
    title: Mapped[str] = mapped_column(String(255), nullable=False,)
    description: Mapped[str | None] = mapped_column(Text, nullable=True,)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority, name='task_priority'), nullable=False,)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, name='task_status'), nullable=False, index=True,)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False,)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True,)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True,)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True,)
    error: Mapped[dict | None] = mapped_column(JSONB, nullable=True,)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0,server_default='0')

    __table_args__ = (
        Index('ix_tasks_status_created', 'status', 'created_at'),
        Index('ix_tasks_priority_created', 'priority', 'created_at'),
    )


class OutboxEvent(Base):
    """Модель таблицы Outbox для хранения отправляемых в Rabbit данных."""

    __tablename__ = 'outbox_events'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True,)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False,)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False,)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False,)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True,)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0',)
