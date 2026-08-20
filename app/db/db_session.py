from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)

from app.core.config import (
    settings,
)


engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=20,
)
SessionLocal = async_scoped_session(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """Получение сессии соединения с БД.

    :return: AsyncSession: сама сессия.
    """
    async with SessionLocal() as session:
        yield session