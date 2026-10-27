"""Demo endpoint: runs the pipeline on demand. Only available in demo mode."""

from fastapi import APIRouter, Depends

from app.api.dependencies import ServicesDep, require_demo_mode
from app.domain.models import PipelineResult

router = APIRouter(prefix="/demo", tags=["demo"], dependencies=[Depends(require_demo_mode)])


@router.post("/run")
def run_pipeline(services: ServicesDep) -> PipelineResult:
    """Fetch the demo emails and analyse them. Running it twice does nothing the second time."""
    return services.pipeline.run()
