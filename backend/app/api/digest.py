"""Digest endpoint: the prioritized summary shown at the top of the dashboard."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import ServicesDep
from app.domain.models import Digest

router = APIRouter(prefix="/digest", tags=["digest"])


@router.get("")
def get_digest(
    services: ServicesDep,
    day: Annotated[
        date | None, Query(description="UTC day, such as 2026-10-26. Default: the latest.")
    ] = None,
) -> Digest:
    """Totals, counts per category, pending drafts and the emails of one day by priority.

    The day is the latest one with mail unless `day` is given. `previous_day` and `next_day`
    name the closest days with mail, so a client can move between days.
    """
    return services.digest.build(day)
