"""Digest endpoint: the prioritized summary shown at the top of the dashboard."""

from fastapi import APIRouter

from app.api.dependencies import ServicesDep
from app.domain.models import Digest

router = APIRouter(prefix="/digest", tags=["digest"])


@router.get("")
def get_digest(services: ServicesDep) -> Digest:
    """Totals, counts per category, pending drafts and the emails of the latest day by priority."""
    return services.digest.build()
