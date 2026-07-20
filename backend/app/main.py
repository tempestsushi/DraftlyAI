from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes.agent import router as agent_router
from .routes.drafts import router as drafts_router
from .routes.evaluations import router as evaluations_router
from .routes.health import router as health_router
from .routes.images import router as images_router
from .routes.integrations import router as integrations_router
from .routes.linkedin import router as linkedin_router
from .routes.logs import router as logs_router
from .routes.topics import router as topics_router
from .store import store


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.initialize()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.frontend_origin == "*" else [settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api_prefix = "/api"

for router in (
    health_router,
    topics_router,
    drafts_router,
    integrations_router,
    images_router,
    evaluations_router,
    logs_router,
    agent_router,
    linkedin_router,
):
    app.include_router(router, prefix=api_prefix)
