"""Tests for the services, running on an in-memory database with the demo and fake providers."""

import pytest

from app.domain.models import Category, DraftStatus, Email, EmailAnalysis, Priority
from app.factory import build_llm_provider, build_mail_provider
from app.providers.llm.fake import FakeLLMProvider
from app.providers.mail.demo import DemoMailProvider
from app.services.analysis import AnalysisService
from app.services.digest import DigestService
from app.services.drafts import DraftNotFoundError, DraftNotPendingError, DraftService
from app.services.ingest import IngestService
from tests.helpers import make_settings


class FailingOnceLLM(FakeLLMProvider):
    """A model that fails on one specific email, to test that the others still get analysed."""

    def __init__(self, failing_id: str) -> None:
        self._failing_id = failing_id

    def analyze_email(self, email: Email) -> EmailAnalysis:
        if email.id == self._failing_id:
            raise RuntimeError("model unavailable")
        return super().analyze_email(email)


@pytest.fixture
def mail():
    return DemoMailProvider()


@pytest.fixture
def analysed_session(session, mail):
    """A session where the 11 demo emails are already ingested and analysed."""
    IngestService(session, mail).run()
    AnalysisService(session, FakeLLMProvider()).run()
    return session


def test_ingest_stores_new_emails_only_once(session, mail):
    service = IngestService(session, mail)
    assert service.run() == 11
    assert service.run() == 0


def test_analysis_creates_one_draft_per_email_that_needs_a_reply(session, mail):
    IngestService(session, mail).run()
    service = AnalysisService(session, FakeLLMProvider())
    assert service.run() == 11
    assert service.run() == 0
    assert len(DraftService(session, mail).list_pending()) == 7


def test_analysis_failure_on_one_email_does_not_block_the_rest(session, mail):
    IngestService(session, mail).run()
    assert AnalysisService(session, FailingOnceLLM("demo-004")).run() == 10
    # The failed email stays pending, so the next run retries it.
    assert AnalysisService(session, FakeLLMProvider()).run() == 1


def test_digest_counts_and_orders_by_priority(analysed_session):
    digest = DigestService(analysed_session).build()
    assert digest.total == 11
    assert digest.counts == {
        Category.URGENT: 3,
        Category.NEEDS_REPLY: 4,
        Category.INFORMATIONAL: 4,
    }
    assert digest.pending_drafts == 7
    priorities = [item.analysis.priority for item in digest.items]
    assert priorities == [Priority.HIGH] * 3 + [Priority.MEDIUM] * 4 + [Priority.LOW] * 4
    # Within a priority, the newest email comes first.
    urgent_dates = [item.email.received_at for item in digest.items[:3]]
    assert urgent_dates == sorted(urgent_dates, reverse=True)


def test_approve_creates_the_draft_in_the_mailbox(analysed_session, mail):
    service = DraftService(analysed_session, mail)
    draft = service.list_pending()[0]
    approved = service.approve(draft.id)
    assert approved.status == DraftStatus.APPROVED
    assert approved.gmail_draft_id == "demo-draft-1"
    assert mail.created_drafts == {"demo-draft-1": draft.body}
    assert len(service.list_pending()) == 6


def test_edited_text_is_what_gets_approved(analysed_session, mail):
    service = DraftService(analysed_session, mail)
    draft = service.list_pending()[0]
    service.edit(draft.id, "My own wording.")
    service.approve(draft.id)
    assert list(mail.created_drafts.values()) == ["My own wording."]


def test_discard_does_not_touch_the_mailbox(analysed_session, mail):
    service = DraftService(analysed_session, mail)
    draft = service.list_pending()[0]
    assert service.discard(draft.id).status == DraftStatus.DISCARDED
    assert mail.created_drafts == {}


def test_a_decided_draft_cannot_change_again(analysed_session, mail):
    service = DraftService(analysed_session, mail)
    draft_id = service.list_pending()[0].id
    service.approve(draft_id)
    for action in (service.approve, service.discard):
        with pytest.raises(DraftNotPendingError):
            action(draft_id)
    with pytest.raises(DraftNotPendingError):
        service.edit(draft_id, "Too late.")


def test_unknown_draft_and_empty_text_are_rejected(analysed_session, mail):
    service = DraftService(analysed_session, mail)
    with pytest.raises(DraftNotFoundError):
        service.approve(9999)
    with pytest.raises(ValueError):
        service.edit(service.list_pending()[0].id, "   ")


def test_factory_builds_demo_providers_in_demo_mode():
    settings = make_settings(demo_mode=True)
    assert isinstance(build_mail_provider(settings), DemoMailProvider)
    assert isinstance(build_llm_provider(settings), FakeLLMProvider)


def test_factory_refuses_real_providers_until_they_exist():
    settings = make_settings(demo_mode=False)
    with pytest.raises(NotImplementedError):
        build_mail_provider(settings)
    with pytest.raises(NotImplementedError):
        build_llm_provider(settings)
