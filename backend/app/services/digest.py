"""Digest service: builds the prioritized summary of the latest day of analysed mail."""

from sqlalchemy.orm import Session

from app.core.dates import utc_day
from app.db.repositories import AnalysisRepository, DraftRepository
from app.domain.models import Category, Digest, DigestItem, DraftStatus, Priority

PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


def sort_for_review(items: list[DigestItem]) -> list[DigestItem]:
    """Highest priority first, newest first within each priority."""
    # sort is stable: sorting by date first keeps that order inside each priority group.
    by_date = sorted(items, key=lambda item: item.email.received_at, reverse=True)
    return sorted(by_date, key=lambda item: PRIORITY_ORDER[item.analysis.priority])


class DigestService:
    """Reads analyses and drafts and puts them in the order the reviewer should see them."""

    def __init__(self, session: Session) -> None:
        self._analyses = AnalysisRepository(session)
        self._drafts = DraftRepository(session)

    def build(self) -> Digest:
        """Return the digest of the day of the newest email, with each email's draft."""
        rows = self._analyses.list_with_emails()
        day = max((utc_day(email.received_at) for email, _ in rows), default=None)
        rows = [(email, analysis) for email, analysis in rows if utc_day(email.received_at) == day]
        drafts = self._drafts.latest_for_emails([email.id for email, _ in rows])
        items = sort_for_review(
            [
                DigestItem(email=email, analysis=analysis, draft=drafts.get(email.id))
                for email, analysis in rows
            ]
        )

        return Digest(
            day=day,
            total=len(items),
            counts={
                category: sum(item.analysis.category == category for item in items)
                for category in Category
            },
            pending_drafts=len(self._drafts.list_by_status(DraftStatus.PROPOSED)),
            items=items,
        )
