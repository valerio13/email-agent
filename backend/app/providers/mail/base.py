"""Mail provider interface: the only way the app reads from and writes to a mailbox."""

from abc import ABC, abstractmethod

from app.domain.models import Email


class MailProvider(ABC):
    """A mailbox. It can read emails and create reply drafts. It can never send an email."""

    @abstractmethod
    def fetch_new(self) -> list[Email]:
        """Return the emails to process. Callers skip the ones they have already stored."""

    @abstractmethod
    def create_draft(self, email: Email, body: str) -> str:
        """Create a reply draft for this email in the mailbox. Return the id of the draft."""
