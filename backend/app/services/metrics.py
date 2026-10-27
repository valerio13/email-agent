"""Metrics service: what the agent did over the last seven days of mail."""

from collections import Counter
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.dates import utc_day
from app.db.repositories import AnalysisRepository, DraftRepository
from app.domain.models import DailyCount, DraftStatus, Metrics

WINDOW_DAYS = 7
# The time saved is an estimate, not a measurement: a fixed number of minutes per item.
MINUTES_PER_EMAIL = 2
MINUTES_PER_DRAFT = 6


class MetricsService:
    """Counts emails and drafts per day and estimates the time the agent saved."""

    def __init__(self, session: Session) -> None:
        self._analyses = AnalysisRepository(session)
        self._drafts = DraftRepository(session)

    def build(self) -> Metrics:
        """Return the metrics for the seven days that end on the day of the newest email."""
        emails = [email for email, _ in self._analyses.list_with_emails()]
        waiting = len(self._drafts.list_by_status(DraftStatus.PROPOSED))
        if not emails:
            return self._metrics(days=[], drafts_created=0, waiting=waiting)

        per_day = Counter(utc_day(email.received_at) for email in emails)
        last_day = max(per_day)
        window = [last_day - timedelta(days=offset) for offset in range(WINDOW_DAYS - 1, -1, -1)]
        window_ids = [email.id for email in emails if utc_day(email.received_at) >= window[0]]
        return self._metrics(
            days=[DailyCount(day=day, emails=per_day[day]) for day in window],
            drafts_created=len(self._drafts.latest_for_emails(window_ids)),
            waiting=waiting,
        )

    @staticmethod
    def _metrics(days: list[DailyCount], drafts_created: int, waiting: int) -> Metrics:
        emails_processed = sum(day.emails for day in days)
        return Metrics(
            days=days,
            emails_processed=emails_processed,
            drafts_created=drafts_created,
            waiting_for_review=waiting,
            minutes_saved=emails_processed * MINUTES_PER_EMAIL + drafts_created * MINUTES_PER_DRAFT,
            minutes_per_email=MINUTES_PER_EMAIL,
            minutes_per_draft=MINUTES_PER_DRAFT,
        )
