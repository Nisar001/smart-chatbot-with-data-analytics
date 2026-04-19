from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.db.base import Base
from app.db.session import engine
from app.middleware.error_handler import register_exception_handlers
from app.routes.router import api_router
from app.sockets.server import socket_app

settings = get_settings()
configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        with open("scripts/create_indexes.sql", "r", encoding="utf-8") as file_pointer:
            for statement in file_pointer.read().split(";"):
                statement = statement.strip()
                if statement:
                    await connection.exec_driver_sql(statement)
    yield


fastapi_app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(fastapi_app)
fastapi_app.include_router(api_router, prefix=settings.api_prefix)

app = socket_app(fastapi_app)
