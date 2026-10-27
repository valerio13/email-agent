"""Mail provider for demo mode: reads fictitious emails from a JSON file."""

import json
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from pydantic import BaseModel, Field

from app.domain.models import Email
from app.providers.mail.base import MailProvider

# demo.py -> mail -> providers -> app -> backend -> project root
DEFAULT_EMAILS_PATH = Path(__file__).resolve().parents[4] / "demo" / "emails.json"


class DemoEmail(BaseModel):
    """One entry of the JSON file: an email placed some days before today instead of on a date."""

    id: str
    sender: str
    subject: str
    body: str
    days_ago: int = Field(ge=0)
    time_utc: time


class DemoMailProvider(MailProvider):
    """A fake mailbox that needs no account. Created drafts are kept in memory.

    The emails are dated relative to the moment they are fetched, so the demo never looks stale.
    """

    def __init__(
        self, emails_path: Path = DEFAULT_EMAILS_PATH, now: datetime | None = None
    ) -> None:
        raw_emails = json.loads(emails_path.read_text(encoding="utf-8"))
        self._entries = [DemoEmail.model_validate(item) for item in raw_emails]
        # now is only for tests, to get fixed dates. It must be timezone-aware and in UTC.
        self._now = now
        self.created_drafts: dict[str, str] = {}

    def fetch_new(self) -> list[Email]:
        """Return every demo email. The caller skips the ones it already has."""
        now = self._now or datetime.now(UTC)
        return [self._to_email(entry, now) for entry in self._entries]

    def create_draft(self, email: Email, body: str) -> str:
        """Keep the draft in memory and return a fake draft id."""
        draft_id = f"demo-draft-{len(self.created_drafts) + 1}"
        self.created_drafts[draft_id] = body
        return draft_id

    @staticmethod
    def _to_email(entry: DemoEmail, now: datetime) -> Email:
        day = (now - timedelta(days=entry.days_ago)).date()
        received_at = datetime.combine(day, entry.time_utc, tzinfo=UTC)
        # An email cannot come from the future: if its time has not come yet, use the day before.
        if received_at > now:
            received_at -= timedelta(days=1)
        return Email(
            id=entry.id,
            sender=entry.sender,
            subject=entry.subject,
            body=entry.body,
            received_at=received_at,
        )
