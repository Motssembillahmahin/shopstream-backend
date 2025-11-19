from fastapi import FastAPI
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware

from services.app.config import app_configs, settings


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator:
    # Startup
    yield
    # Shutdown


app = FastAPI(
    **app_configs,
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGINS_REGEX,
    allow_credentials=True,
    allow_methods=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
    allow_headers=settings.CORS_HEADERS,
)
