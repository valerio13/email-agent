"""FastAPI application: mounts the API, runs the scheduler and maps service errors to HTTP."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import get_session_factory
from app.factory import get_llm_provider, get_mail_provider
from app.scheduler import create_scheduler
from app.services.drafts import DraftNotFoundError, DraftNotPendingError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# main.py -> app -> backend -> project root. The Docker image keeps the same layout.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Start the daily scheduler with the app and stop it on shutdown."""
    settings = get_settings()
    scheduler = None
    if settings.scheduler_enabled:
        scheduler = create_scheduler(
            settings, get_session_factory(), get_mail_provider(), get_llm_provider()
        )
        scheduler.start()
        logger.info(
            "Daily run scheduled at %s (%s).", settings.schedule_time, settings.schedule_timezone
        )
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="Email agent",
    description="Daily prioritized email summary and reply drafts, approved by a human.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(api_router)


@app.exception_handler(DraftNotFoundError)
def draft_not_found(request: Request, exc: DraftNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DraftNotPendingError)
def draft_not_pending(request: Request, exc: DraftNotPendingError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


def serve_frontend(app: FastAPI, directory: Path) -> None:
    """Serve the built dashboard at / when it exists, so one process and one port serve both.

    API routes are checked first, and an unknown /api path still answers a JSON 404. Without a
    build (development, tests) only the API runs and the dashboard comes from the Vite server.
    """
    if directory.is_dir():
        app.frontend("/", directory=directory)


serve_frontend(app, FRONTEND_DIST)
