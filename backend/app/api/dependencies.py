"""Dependencies shared by the routers: database session, services and the demo-mode guard."""

from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.factory import Services, build_services, get_llm_provider, get_mail_provider

SessionDep = Annotated[Session, Depends(get_session)]


def get_services(session: SessionDep) -> Services:
    """Build the services for one request, all sharing that request's database session."""
    return build_services(session, get_mail_provider(), get_llm_provider())


ServicesDep = Annotated[Services, Depends(get_services)]


def require_demo_mode(settings: Annotated[Settings, Depends(get_settings)]) -> None:
    """Reject the request unless the app runs in demo mode."""
    if not settings.demo_mode:
        raise HTTPException(status_code=403, detail="This endpoint is only available in demo mode.")
