"""Gmail provider tests. A fake Gmail client answers from memory: no account, no network."""

import base64
import email
from datetime import UTC, datetime
from email import policy
from typing import Any

import pytest

from app.domain.models import Email
from app.factory import build_services
from app.providers.llm.fake import FakeLLMProvider
from app.providers.mail.gmail import MAX_BODY_CHARS, GmailMailProvider


def b64(text: str) -> str:
    """Encode like Gmail does: base64url without the trailing = padding."""
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def message(
    message_id: str,
    *,
    sender: str = "Marcus Lee <marcus.lee@northwind.example.com>",
    subject: str | None = "Production API is down",
    text: str | None = "Our integration is returning errors.",
    html: str | None = None,
    extra_headers: dict[str, str] | None = None,
    thread_id: str = "thread-1",
) -> dict[str, Any]:
    """A message as the Gmail API returns it with format=full."""
    headers = {"From": sender, **(extra_headers or {})}
    if subject is not None:
        headers["Subject"] = subject
    parts = []
    if text is not None:
        parts.append({"mimeType": "text/plain", "body": {"data": b64(text)}})
    if html is not None:
        parts.append({"mimeType": "text/html", "body": {"data": b64(html)}})
    return {
        "id": message_id,
        "threadId": thread_id,
        # 2026-10-26 09:14:00 UTC, in milliseconds as a string, as Gmail sends it.
        "internalDate": str(int(datetime(2026, 10, 26, 9, 14, tzinfo=UTC).timestamp() * 1000)),
        "payload": {
            "mimeType": "multipart/alternative",
            "headers": [{"name": k, "value": v} for k, v in headers.items()],
            "parts": parts,
        },
    }


class Request:
    def __init__(self, result: dict[str, Any]) -> None:
        self._result = result

    def execute(self) -> dict[str, Any]:
        return self._result


class FakeGmail:
    """Just enough of the Gmail client: users().messages().list/get and users().drafts().create."""

    def __init__(self, *messages: dict[str, Any]) -> None:
        self.by_id = {m["id"]: m for m in messages}
        self.searches: list[tuple[str, int]] = []
        self.created: list[dict[str, Any]] = []

    def users(self):
        return self

    def messages(self):
        gmail = self

        class Messages:
            def list(self, userId: str, q: str, maxResults: int):
                gmail.searches.append((q, maxResults))
                return Request({"messages": [{"id": message_id} for message_id in gmail.by_id]})

            # metadataHeaders is not annotated: inside this class, `list` is the method above.
            def get(self, userId: str, id: str, format: str, metadataHeaders=None):
                return Request(gmail.by_id[id])

        return Messages()

    def drafts(self):
        gmail = self

        class Drafts:
            def create(self, userId: str, body: dict[str, Any]):
                gmail.created.append(body)
                return Request({"id": f"gmail-draft-{len(gmail.created)}"})

        return Drafts()


def parse_draft(gmail: FakeGmail, index: int = 0):
    """The reply that was saved as a draft, parsed back from its raw form."""
    raw = gmail.created[index]["message"]["raw"]
    return email.message_from_bytes(base64.urlsafe_b64decode(raw), policy=policy.default)


def test_fetch_new_turns_gmail_messages_into_emails():
    gmail = FakeGmail(message("msg-1"))
    provider = GmailMailProvider(gmail, query="in:inbox newer_than:1d", max_emails=10)

    [received] = provider.fetch_new()

    assert gmail.searches == [("in:inbox newer_than:1d", 10)]
    assert received == Email(
        id="msg-1",
        sender="Marcus Lee <marcus.lee@northwind.example.com>",
        subject="Production API is down",
        body="Our integration is returning errors.",
        received_at=datetime(2026, 10, 26, 9, 14, tzinfo=UTC),
    )


def test_the_plain_text_version_wins_over_the_html_one():
    gmail = FakeGmail(message("msg-1", text="Plain version.", html="<p>HTML version.</p>"))
    assert GmailMailProvider(gmail).fetch_new()[0].body == "Plain version."


def test_an_html_only_email_is_read_as_text_without_scripts_or_styles():
    html = (
        "<html><style>p { color: red }</style><body><p>Hello <b>there</b>,</p>"
        "<script>track()</script><div>Can you send the quote?</div></body></html>"
    )
    gmail = FakeGmail(message("msg-1", text=None, html=html))

    body = GmailMailProvider(gmail).fetch_new()[0].body

    assert "Hello there," in body
    assert "Can you send the quote?" in body
    assert "color" not in body
    assert "track()" not in body
    assert "<" not in body


def test_encoded_subjects_and_missing_subjects_are_handled():
    gmail = FakeGmail(
        message("msg-1", subject="=?UTF-8?B?UHLDvGZ1bmcgZGVyIFJlY2hudW5n?="),
        message("msg-2", subject=None),
    )
    first, second = GmailMailProvider(gmail).fetch_new()
    assert first.subject == "Prüfung der Rechnung"
    assert second.subject == "(no subject)"


def test_a_huge_email_is_cut_to_the_limit():
    gmail = FakeGmail(message("msg-1", text="x" * (MAX_BODY_CHARS + 5000)))
    assert len(GmailMailProvider(gmail).fetch_new()[0].body) == MAX_BODY_CHARS


def test_an_empty_inbox_gives_no_emails():
    assert GmailMailProvider(FakeGmail()).fetch_new() == []


def test_draft_is_a_reply_inside_the_same_thread():
    gmail = FakeGmail(
        message(
            "msg-1",
            extra_headers={
                "Message-ID": "<abc@mail.example.com>",
                "References": "<first@mail.example.com>",
            },
            thread_id="thread-42",
        )
    )
    provider = GmailMailProvider(gmail)
    original = provider.fetch_new()[0]

    draft_id = provider.create_draft(original, "On it, calling you now.")

    assert draft_id == "gmail-draft-1"
    assert gmail.created[0]["message"]["threadId"] == "thread-42"
    reply = parse_draft(gmail)
    assert reply["To"] == "Marcus Lee <marcus.lee@northwind.example.com>"
    assert reply["Subject"] == "Re: Production API is down"
    assert reply["In-Reply-To"] == "<abc@mail.example.com>"
    assert reply["References"] == "<first@mail.example.com> <abc@mail.example.com>"
    assert reply.get_content().strip() == "On it, calling you now."


def test_draft_goes_to_the_reply_to_address_when_there_is_one():
    gmail = FakeGmail(message("msg-1", extra_headers={"Reply-To": "support@northwind.example.com"}))
    provider = GmailMailProvider(gmail)
    provider.create_draft(provider.fetch_new()[0], "Thanks.")
    assert parse_draft(gmail)["To"] == "support@northwind.example.com"


def test_draft_subject_is_not_prefixed_twice():
    gmail = FakeGmail(message("msg-1", subject="Re: Invoice 2041"))
    provider = GmailMailProvider(gmail)
    provider.create_draft(provider.fetch_new()[0], "Paid today.")
    assert parse_draft(gmail)["Subject"] == "Re: Invoice 2041"


def test_a_header_with_a_line_break_cannot_inject_other_headers():
    injected = "a@example.com\nBcc: victim@example.com"
    gmail = FakeGmail(message("msg-1", extra_headers={"Reply-To": injected}))
    provider = GmailMailProvider(gmail)
    with pytest.raises(ValueError):
        provider.create_draft(provider.fetch_new()[0], "Hello.")
    assert gmail.created == []


def test_the_whole_pipeline_works_on_gmail_and_approval_creates_a_gmail_draft(session):
    gmail = FakeGmail(
        message("msg-1", text="Could you send us a quote?", thread_id="thread-7"),
        message("msg-2", sender="News <news@example.com>", subject="Weekly digest", text="News."),
    )
    mail = GmailMailProvider(gmail)
    services = build_services(session, mail, FakeLLMProvider())

    result = services.pipeline.run()
    assert (result.new_emails, result.analysed) == (2, 2)
    [pending] = services.drafts.list_pending()
    assert pending.email.id == "msg-1"
    # Nothing reaches Gmail until a human approves.
    assert gmail.created == []

    approved = services.drafts.approve(pending.draft.id)

    assert approved.gmail_draft_id == "gmail-draft-1"
    assert gmail.created[0]["message"]["threadId"] == "thread-7"
