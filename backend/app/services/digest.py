"""Digest service: builds the prioritized summary of all analysed emails."""

from sqlalchemy.orm import Session

from app.db.repositories import AnalysisRepository, DraftRepository
from app.domain.models import Category, Digest, DigestItem, DraftStatus, Priority

PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


class DigestService:
    """Reads analyses and drafts and puts them in the order the reviewer should see them."""

    def __init__(self, session: Session) -> None:
        self._analyses = AnalysisRepository(session)
        self._drafts = DraftRepository(session)

    def build(self) -> Digest:
        """Return the digest: highest priority first, newest first within each priority."""
        items = [
            DigestItem(email=email, analysis=analysis)
            for email, analysis in self._analyses.list_with_emails()
        ]
        # sort is stable: sorting by date first keeps that order inside each priority group.
        items.sort(key=lambda item: item.email.received_at, reverse=True)
        items.sort(key=lambda item: PRIORITY_ORDER[item.analysis.priority])

        return Digest(
            total=len(items),
            counts={
                category: sum(item.analysis.category == category for item in items)
                for category in Category
            },
            pending_drafts=len(self._drafts.list_by_status(DraftStatus.PROPOSED)),
            items=items,
        )
