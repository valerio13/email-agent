"""FastAPI application: mounts the API and turns service errors into HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.services.drafts import DraftNotFoundError, DraftNotPendingError

app = FastAPI(
    title="Email agent",
    description="Daily prioritized email summary and reply drafts, approved by a human.",
    version="0.1.0",
)
app.include_router(api_router)


@app.exception_handler(DraftNotFoundError)
def draft_not_found(request: Request, exc: DraftNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DraftNotPendingError)
def draft_not_pending(request: Request, exc: DraftNotPendingError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})
