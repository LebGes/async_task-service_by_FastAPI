from functools import (
    lru_cache,
)

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    """Конфигурация приложения, загружается из переменных окружения."""

    model_config = SettingsConfigDict(env_file='.env.example', extra='ignore')

    database_url: str = 'postgresql+asyncpg://tasks:tasks@localhost:5432/tasks_db'
    rabbitmq_url: str = 'amqp://tasks:tasks@localhost:5672/'
    tasks_queue: str = 'tasks'
    rabbitmq_exchange: str = 'tasks'
    rabbitmq_prefetch: int = 10
    worker_concurrency: int = 10
    outbox_poll_interval: float = 1.0
    task_retry_limit: int = 3
    task_retry_delay: float = 2.0

    model_config = SettingsConfigDict(env_file='.env.example', env_file_encoding='utf-8', extra='ignore')


@lru_cache
def get_settings() -> Settings:
    """Получение конфигурационных данных приложения.

    :return: Settings: Конфигурационные данные приложения.
    """

    return Settings()


settings = get_settings()