"""Ingest service: copies new mail from the mailbox into the database."""

from sqlalchemy.orm import Session

from app.db.repositories import EmailRepository
from app.providers.mail.base import MailProvider


class IngestService:
    """Fetches mail through a MailProvider and stores the emails the database does not have."""

    def __init__(self, session: Session, mail: MailProvider) -> None:
        self._session = session
        self._mail = mail
        self._emails = EmailRepository(session)

    def run(self) -> int:
        """Store the new emails and return how many there were."""
        new_emails = 0
        for email in self._mail.fetch_new():
            if self._emails.add_if_new(email):
                new_emails += 1
        self._session.commit()
        return new_emails
