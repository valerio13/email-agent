"""Demo service: loads the demo data, keeps its dates current and resets it."""

from sqlalchemy.orm import Session

from app.core.dates import utc_day
from app.db.repositories import EmailRepository
from app.domain.models import PipelineResult
from app.providers.mail.base import MailProvider
from app.services.pipeline import PipelineService


class DemoService:
    """Runs the demo pipeline and wipes the demo data. Only used in demo mode."""

    def __init__(self, session: Session, mail: MailProvider, pipeline: PipelineService) -> None:
        self._session = session
        self._mail = mail
        self._pipeline = pipeline
        self._emails = EmailRepository(session)

    def run(self) -> PipelineResult:
        """Run the pipeline. If the stored emails are from an earlier day, start over first."""
        if self._is_stale():
            return self.reset()
        return self._pipeline.run()

    def reset(self) -> PipelineResult:
        """Delete every email, analysis and draft, then load the demo emails again."""
        self._emails.delete_all()
        self._session.commit()
        return self._pipeline.run()

    def _is_stale(self) -> bool:
        """True when the mailbox now offers mail from a later day than the one stored."""
        stored = self._emails.latest_received_at()
        offered = max((email.received_at for email in self._mail.fetch_new()), default=None)
        if stored is None or offered is None:
            return False
        return utc_day(offered) > utc_day(stored)
