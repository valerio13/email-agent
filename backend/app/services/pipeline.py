"""Pipeline service: the run that fetches new mail and analyses it, by schedule or on demand."""

import threading

from app.domain.models import PipelineResult
from app.services.analysis import AnalysisService
from app.services.ingest import IngestService

# Services are built for each request, so the lock lives here, shared by all of them. It works
# because the API runs a single worker, as the scheduler already requires.
_run_lock = threading.Lock()


class PipelineBusyError(Exception):
    """A run is already in progress, so a second one would repeat its work."""


class PipelineService:
    """Fetches the new mail and then analyses it."""

    def __init__(self, ingest: IngestService, analysis: AnalysisService) -> None:
        self._ingest = ingest
        self._analysis = analysis

    def run(self) -> PipelineResult:
        """Ingest first, so the analysis also sees the emails that just arrived.

        Only one run at a time: the daily job and a click on the dashboard could overlap, and both
        would analyse the same emails.
        """
        if not _run_lock.acquire(blocking=False):
            raise PipelineBusyError("A run is already in progress. Wait for it to finish.")
        try:
            new_emails = self._ingest.run()
            analysed = self._analysis.run()
        finally:
            _run_lock.release()
        return PipelineResult(new_emails=new_emails, analysed=analysed)
