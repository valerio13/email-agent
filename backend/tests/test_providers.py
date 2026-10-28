"""Tests for the mail and LLM providers used in demo mode and in tests."""

import inspect
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.models import Category, Priority
from app.providers.llm.fake import FakeLLMProvider
from app.providers.mail.base import MailProvider
from app.providers.mail.demo import DemoMailProvider
from app.providers.mail.gmail import GmailMailProvider
from tests.helpers import DEMO_NOW


@pytest.fixture
def emails():
    return DemoMailProvider(now=DEMO_NOW).fetch_new()


def public_method_names(cls: type) -> list[str]:
    return [
        name for name, _ in inspect.getmembers(cls, inspect.isfunction) if not name.startswith("_")
    ]


@pytest.mark.parametrize("cls", [MailProvider, DemoMailProvider, GmailMailProvider])
def test_mail_providers_cannot_send_email(cls):
    assert not [name for name in public_method_names(cls) if "send" in name.lower()]


def test_demo_provider_returns_unique_valid_emails(emails):
    assert len(emails) == 36
    assert len({email.id for email in emails}) == len(emails)


def test_demo_dates_are_relative_to_now(emails):
    by_id = {email.id: email for email in emails}
    assert by_id["demo-001"].received_at == datetime(2026, 10, 26, 9, 14, tzinfo=UTC)
    assert by_id["demo-011"].received_at == datetime(2026, 10, 23, 15, 30, tzinfo=UTC)
    # A week later, the same file gives dates a week later.
    later = DemoMailProvider(now=DEMO_NOW + timedelta(days=7)).fetch_new()
    assert later[0].received_at == datetime(2026, 11, 2, 9, 14, tzinfo=UTC)


def test_demo_emails_cover_seven_days(emails):
    assert len({email.received_at.date() for email in emails}) == 7


def test_demo_emails_are_never_from_the_future():
    early = datetime(2026, 10, 26, 3, 0, tzinfo=UTC)
    emails = DemoMailProvider(now=early).fetch_new()
    assert all(email.received_at <= early for email in emails)


def test_demo_provider_keeps_created_drafts(emails):
    provider = DemoMailProvider()
    draft_id = provider.create_draft(emails[0], "Hello")
    assert provider.created_drafts == {draft_id: "Hello"}


def test_fake_llm_classifies_every_demo_email(emails):
    llm = FakeLLMProvider()
    categories = [llm.analyze_email(email).category for email in emails]
    assert categories.count(Category.URGENT) == 7
    assert categories.count(Category.NEEDS_REPLY) == 14
    assert categories.count(Category.INFORMATIONAL) == 15


def test_fake_llm_urgent_email_gets_high_priority_and_a_draft(emails):
    analysis = FakeLLMProvider().analyze_email(emails[0])
    assert analysis.priority == Priority.HIGH
    assert analysis.needs_reply
    assert analysis.draft_reply.startswith("Hi Marcus,")


def test_fake_llm_informational_email_has_no_draft(emails):
    analysis = FakeLLMProvider().analyze_email(emails[7])
    assert analysis.category == Category.INFORMATIONAL
    assert not analysis.needs_reply
    assert analysis.draft_reply is None
