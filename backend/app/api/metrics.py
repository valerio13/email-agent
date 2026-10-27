"""Metrics endpoint: what the agent did over the last seven days."""

from fastapi import APIRouter

from app.api.dependencies import ServicesDep
from app.domain.models import Metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
def get_metrics(services: ServicesDep) -> Metrics:
    """Emails per day, drafts created, drafts waiting for review and the estimated time saved."""
    return services.metrics.build()
