"""Database connection: a shared engine, a session factory and a per-request session."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Return the shared SQLAlchemy engine, built once on first use."""
    url = get_settings().database_url.get_secret_value()
    # pool_pre_ping tests each connection before use, so a restarted database does not break us.
    return create_engine(url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Return the shared session factory. It does not open any session yet."""
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Yield a session and close it afterwards. Meant to be used as a FastAPI dependency.

    Callers commit explicitly. Anything left uncommitted is rolled back when the session closes.
    """
    session_factory = get_session_factory()
    with session_factory() as session:
        yield session
