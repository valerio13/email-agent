"""Repositories: save and read domain models so services never deal with SQL or tables.

Repositories never commit. The caller (a service) decides when to commit or roll back.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalysisRecord, DraftRecord, EmailRecord
from app.domain.models import Draft, DraftStatus, Email, EmailAnalysis


class EmailRepository:
    """Stores and reads received emails."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_if_new(self, email: Email) -> bool:
        """Store the email unless its id is already known. Return True if it was stored."""
        if self._session.get(EmailRecord, email.id) is not None:
            return False
        self._session.add(EmailRecord(**email.model_dump()))
        # flush sends the INSERT now, so later checks in the same transaction see this email.
        self._session.flush()
        return True

    def get(self, email_id: str) -> Email | None:
        """Return the email with this id, or None."""
        record = self._session.get(EmailRecord, email_id)
        return Email.model_validate(record) if record else None

    def list_without_analysis(self) -> list[Email]:
        """Return the emails that have not been analysed yet, oldest first."""
        stmt = (
            select(EmailRecord).where(~EmailRecord.analysis.has()).order_by(EmailRecord.received_at)
        )
        return [Email.model_validate(record) for record in self._session.scalars(stmt)]


class AnalysisRepository:
    """Stores and reads the analysis of each email."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, email_id: str, analysis: EmailAnalysis) -> None:
        """Store the analysis of an email. Each email can have only one analysis."""
        self._session.add(AnalysisRecord(email_id=email_id, **analysis.model_dump()))
        self._session.flush()

    def get(self, email_id: str) -> EmailAnalysis | None:
        """Return the analysis of this email, or None."""
        stmt = select(AnalysisRecord).where(AnalysisRecord.email_id == email_id)
        record = self._session.scalars(stmt).first()
        return EmailAnalysis.model_validate(record) if record else None


class DraftRepository:
    """Stores and reads the reply drafts waiting for human review."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, email_id: str, body: str) -> Draft:
        """Create a draft in the PROPOSED status for an email."""
        record = DraftRecord(email_id=email_id, body=body)
        self._session.add(record)
        self._session.flush()
        # refresh loads the values the database fills in, such as created_at.
        self._session.refresh(record)
        return Draft.model_validate(record)

    def get(self, draft_id: int) -> Draft | None:
        """Return the draft with this id, or None."""
        record = self._session.get(DraftRecord, draft_id)
        return Draft.model_validate(record) if record else None

    def list_by_status(self, status: DraftStatus) -> list[Draft]:
        """Return the drafts in this status, oldest first."""
        stmt = (
            select(DraftRecord).where(DraftRecord.status == status).order_by(DraftRecord.created_at)
        )
        return [Draft.model_validate(record) for record in self._session.scalars(stmt)]

    def update_body(self, draft_id: int, body: str) -> Draft | None:
        """Replace the text of a draft. Return the updated draft, or None if it does not exist."""
        record = self._session.get(DraftRecord, draft_id)
        if record is None:
            return None
        record.body = body
        self._session.flush()
        self._session.refresh(record)
        return Draft.model_validate(record)

    def set_status(
        self, draft_id: int, status: DraftStatus, gmail_draft_id: str | None = None
    ) -> Draft | None:
        """Change the status of a draft, optionally storing the id of the draft created in Gmail.

        Return the updated draft, or None if it does not exist.
        """
        record = self._session.get(DraftRecord, draft_id)
        if record is None:
            return None
        record.status = status
        if gmail_draft_id is not None:
            record.gmail_draft_id = gmail_draft_id
        self._session.flush()
        self._session.refresh(record)
        return Draft.model_validate(record)
