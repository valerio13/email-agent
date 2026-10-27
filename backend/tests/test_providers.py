"""Tests for the mail and LLM providers used in demo mode and in tests."""

import inspect

import pytest

from app.domain.models import Category, Priority
from app.providers.llm.fake import FakeLLMProvider
from app.providers.mail.base import MailProvider
from app.providers.mail.demo import DemoMailProvider


@pytest.fixture
def emails():
    return DemoMailProvider().fetch_new()


def public_method_names(cls: type) -> list[str]:
    return [
        name for name, _ in inspect.getmembers(cls, inspect.isfunction) if not name.startswith("_")
    ]


@pytest.mark.parametrize("cls", [MailProvider, DemoMailProvider])
def test_mail_providers_cannot_send_email(cls):
    assert not [name for name in public_method_names(cls) if "send" in name.lower()]


def test_demo_provider_returns_unique_valid_emails(emails):
    assert len(emails) == 11
    assert len({email.id for email in emails}) == len(emails)


def test_demo_provider_keeps_created_drafts(emails):
    provider = DemoMailProvider()
    draft_id = provider.create_draft(emails[0], "Hello")
    assert provider.created_drafts == {draft_id: "Hello"}


def test_fake_llm_classifies_every_demo_email(emails):
    llm = FakeLLMProvider()
    categories = [llm.analyze_email(email).category for email in emails]
    assert categories.count(Category.URGENT) == 3
    assert categories.count(Category.NEEDS_REPLY) == 4
    assert categories.count(Category.INFORMATIONAL) == 4


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
