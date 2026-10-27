"""Mail provider for demo mode: reads fictitious emails from a JSON file."""

import json
from pathlib import Path

from app.domain.models import Email
from app.providers.mail.base import MailProvider

# demo.py -> mail -> providers -> app -> backend -> project root
DEFAULT_EMAILS_PATH = Path(__file__).resolve().parents[4] / "demo" / "emails.json"


class DemoMailProvider(MailProvider):
    """A fake mailbox that needs no account. Created drafts are kept in memory."""

    def __init__(self, emails_path: Path = DEFAULT_EMAILS_PATH) -> None:
        raw_emails = json.loads(emails_path.read_text(encoding="utf-8"))
        self._emails = [Email.model_validate(item) for item in raw_emails]
        self.created_drafts: dict[str, str] = {}

    def fetch_new(self) -> list[Email]:
        """Return every demo email. The caller skips the ones it already has."""
        return list(self._emails)

    def create_draft(self, email: Email, body: str) -> str:
        """Keep the draft in memory and return a fake draft id."""
        draft_id = f"demo-draft-{len(self.created_drafts) + 1}"
        self.created_drafts[draft_id] = body
        return draft_id
