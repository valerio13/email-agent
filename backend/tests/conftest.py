from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.models import Base


@pytest.fixture
def session() -> Iterator[Session]:
    """A session on a throwaway in-memory database, so tests need no Docker or .env."""
    # StaticPool keeps one shared connection, so API tests see the same data from every thread.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()
