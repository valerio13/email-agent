"""Mail provider for real mode: reads the inbox and creates reply drafts through the Gmail API."""

import base64
import re
from datetime import UTC, datetime
from email.header import decode_header, make_header
from email.message import EmailMessage
from html.parser import HTMLParser
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import Settings
from app.domain.models import Email
from app.providers.mail.base import MailProvider

# readonly reads the inbox and compose creates drafts. Google also lets compose send mail, so the
# promise that nothing is sent rests on this class having no send operation (and a test that
# checks it), not on the scopes.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]
TOKEN_URI = "https://oauth2.googleapis.com/token"
# A very long email would cost a lot to analyse and says little more than its first pages.
MAX_BODY_CHARS = 20_000


def build_gmail_service(settings: Settings) -> Any:
    """Build the Gmail API client from the client id, secret and refresh token in the settings."""
    client_secret = settings.google_client_secret.get_secret_value()
    refresh_token = settings.google_refresh_token.get_secret_value()
    if not (settings.google_client_id and client_secret and refresh_token):
        raise RuntimeError(
            "Gmail mode needs GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and GOOGLE_REFRESH_TOKEN. "
            "Run `uv run python -m app.cli authorize-gmail` to get the last one."
        )
    # There is no access token yet: the library asks Google for one with the refresh token.
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=settings.google_client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    # cache_discovery=False: the discovery cache needs a writable folder and an old package.
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def _header(headers: list[dict[str, str]], name: str) -> str:
    """Return a header decoded to text ("" if absent). Subjects often arrive as =?UTF-8?B?...?=."""
    for header in headers:
        if header["name"].lower() == name.lower():
            return str(make_header(decode_header(header["value"]))).strip()
    return ""


def _decode(data: str) -> str:
    """Gmail sends body data as base64url, usually without the trailing = padding."""
    raw = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
    return raw.decode("utf-8", errors="replace")


def _find_part(payload: dict[str, Any], mime_type: str) -> str | None:
    """Return the text of the first part of this type, searching nested multipart parts."""
    data = payload.get("body", {}).get("data")
    if payload.get("mimeType") == mime_type and data:
        return _decode(data)
    for part in payload.get("parts", []):
        found = _find_part(part, mime_type)
        if found is not None:
            return found
    return None


class _TextExtractor(HTMLParser):
    """Keeps the visible text of an HTML email: no tags, scripts or styles."""

    BREAKS = {"br", "p", "div", "tr", "li", "h1", "h2", "h3"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._hidden += 1
        elif tag in self.BREAKS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._hidden:
            self._hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self._hidden:
            self._parts.append(data)

    def text(self) -> str:
        joined = re.sub(r"[ \t]+", " ", "".join(self._parts))
        return re.sub(r"\n\s*\n+", "\n\n", joined).strip()


def _body(payload: dict[str, Any]) -> str:
    """The plain text of an email, or the text of its HTML when it has no plain version."""
    text = _find_part(payload, "text/plain")
    if text is None:
        markup = _find_part(payload, "text/html")
        if markup is None:
            return ""
        extractor = _TextExtractor()
        extractor.feed(markup)
        text = extractor.text()
    return text.strip()[:MAX_BODY_CHARS]


def _reply_subject(subject: str) -> str:
    return subject if subject.lower().startswith("re:") else f"Re: {subject}"


class GmailMailProvider(MailProvider):
    """A real Gmail mailbox. It reads the inbox and creates drafts. It has no way to send."""

    def __init__(
        self, service: Any, query: str = "in:inbox newer_than:2d", max_emails: int = 50
    ) -> None:
        self._service = service
        self._query = query
        self._max_emails = max_emails

    def fetch_new(self) -> list[Email]:
        """Return the emails that match the query. The caller skips the ones it already has."""
        messages = self._service.users().messages()
        listing = messages.list(userId="me", q=self._query, maxResults=self._max_emails).execute()
        return [
            self._to_email(messages.get(userId="me", id=ref["id"], format="full").execute())
            for ref in listing.get("messages", [])
        ]

    def create_draft(self, email: Email, body: str) -> str:
        """Create a reply in the same Gmail thread as a draft. Return the id of the draft."""
        # The thread and the original Message-ID are fetched now, so the stored email does not
        # need them. They make Gmail show the draft inside the conversation.
        original = (
            self._service.users()
            .messages()
            .get(
                userId="me",
                id=email.id,
                format="metadata",
                metadataHeaders=["Message-ID", "References", "Reply-To", "From"],
            )
            .execute()
        )
        headers = original.get("payload", {}).get("headers", [])
        reply = EmailMessage()
        reply["To"] = _header(headers, "Reply-To") or _header(headers, "From") or email.sender
        reply["Subject"] = _reply_subject(email.subject)
        message_id = _header(headers, "Message-ID")
        if message_id:
            reply["In-Reply-To"] = message_id
            reply["References"] = f"{_header(headers, 'References')} {message_id}".strip()
        reply.set_content(body)

        raw = base64.urlsafe_b64encode(reply.as_bytes()).decode()
        draft = (
            self._service.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw, "threadId": original["threadId"]}})
            .execute()
        )
        return str(draft["id"])

    @staticmethod
    def _to_email(message: dict[str, Any]) -> Email:
        payload = message["payload"]
        headers = payload.get("headers", [])
        return Email(
            id=message["id"],
            sender=_header(headers, "From") or "unknown sender",
            subject=_header(headers, "Subject") or "(no subject)",
            body=_body(payload),
            # internalDate is when Gmail received the email, in milliseconds since 1970.
            received_at=datetime.fromtimestamp(int(message["internalDate"]) / 1000, tz=UTC),
        )
