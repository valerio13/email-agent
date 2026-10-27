"""The API router: every endpoint lives under /api."""

from fastapi import APIRouter

from app.api import demo, digest, drafts

api_router = APIRouter(prefix="/api")
api_router.include_router(digest.router)
api_router.include_router(drafts.router)
api_router.include_router(demo.router)
