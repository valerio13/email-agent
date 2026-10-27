"""Demo endpoints: load or reset the demo data on demand. Only available in demo mode."""

from fastapi import APIRouter, Depends

from app.api.dependencies import ServicesDep, require_demo_mode
from app.domain.models import PipelineResult

router = APIRouter(prefix="/demo", tags=["demo"], dependencies=[Depends(require_demo_mode)])


@router.post("/run")
def run_demo(services: ServicesDep) -> PipelineResult:
    """Fetch the demo emails and analyse them. A second run on the same day does nothing."""
    return services.demo.run()


@router.post("/reset")
def reset_demo(services: ServicesDep) -> PipelineResult:
    """Delete all the data and load the demo emails again, dated relative to today."""
    return services.demo.reset()
