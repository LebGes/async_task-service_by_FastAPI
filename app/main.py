from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.db_session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Async Task Service",
    version="1.0.0",
)


@app.get('/health', tags=['health'])
async def health():
    return {'status': 'ok'}


@app.get('/ready', tags=['health'])
async def ready():
    return {'status': 'ready', 'enviroment': settings.environment}
