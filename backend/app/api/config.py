"""Config endpoint: what the dashboard needs to know about how the app runs."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings

router = APIRouter(prefix="/config", tags=["config"])


class AppConfig(BaseModel):
    """Settings the dashboard may read. Nothing secret goes here."""

    demo_mode: bool


@router.get("")
def get_app_config(settings: Annotated[Settings, Depends(get_settings)]) -> AppConfig:
    """Whether the app runs on demo data, so the dashboard can show its demo buttons."""
    return AppConfig(demo_mode=settings.demo_mode)
