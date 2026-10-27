"""Pipeline service: the daily run, used by the scheduler and by the demo endpoint."""

from app.domain.models import PipelineResult
from app.services.analysis import AnalysisService
from app.services.ingest import IngestService


class PipelineService:
    """Fetches the new mail and then analyses it."""

    def __init__(self, ingest: IngestService, analysis: AnalysisService) -> None:
        self._ingest = ingest
        self._analysis = analysis

    def run(self) -> PipelineResult:
        """Ingest first, so the analysis also sees the emails that just arrived."""
        new_emails = self._ingest.run()
        analysed = self._analysis.run()
        return PipelineResult(new_emails=new_emails, analysed=analysed)
