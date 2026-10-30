"""Pipeline endpoint: fetch and analyse the new mail now, without waiting for the daily run."""

from fastapi import APIRouter

from app.api.dependencies import ServicesDep
from app.domain.models import PipelineResult

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/run")
def run_pipeline(services: ServicesDep) -> PipelineResult:
    """Fetch the new emails and analyse them. It answers when the run is over, which can take a
    minute with a real model. 409 if another run is still in progress."""
    return services.pipeline.run()
