"""Tests for the services, running on an in-memory database with the demo and fake providers."""

from datetime import date, timedelta

import pytest

from app.core.dates import utc_day
from app.db.repositories import EmailRepository
from app.domain.models import (
    Category,
    DraftStatus,
    Email,
    EmailAnalysis,
    PipelineResult,
    Priority,
)
from app.factory import build_llm_provider, build_mail_provider
from app.providers.llm.fake import FakeLLMProvider
from app.providers.llm.langchain_provider import LangChainLLMProvider
from app.providers.mail.demo import DemoMailProvider
from app.providers.mail.gmail import GmailMailProvider
from app.services.analysis import AnalysisService
from app.services.demo import DemoService
from app.services.digest import DigestService
from app.services.drafts import (
    DraftNotDiscardedError,
    DraftNotFoundError,
    DraftNotPendingError,
    DraftService,
)
from app.services.ingest import IngestService
from app.services.metrics import MINUTES_PER_DRAFT, MINUTES_PER_EMAIL, MetricsService
from app.services.pipeline import PipelineService
from tests.helpers import DEMO_NOW, make_settings


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
    return DemoMailProvider(now=DEMO_NOW)


@pytest.fixture
def analysed_session(session, mail):
    """A session where the 36 demo emails are already ingested and analysed."""
    IngestService(session, mail).run()
    AnalysisService(session, FakeLLMProvider()).run()
    return session


def make_demo_service(session, mail) -> DemoService:
    ingest = IngestService(session, mail)
    pipeline = PipelineService(ingest, AnalysisService(session, FakeLLMProvider()))
    return DemoService(session, mail, pipeline)


def test_ingest_stores_new_emails_only_once(session, mail):
    service = IngestService(session, mail)
    assert service.run() == 36
    assert service.run() == 0


def test_analysis_creates_one_draft_per_email_that_needs_a_reply(session, mail):
    IngestService(session, mail).run()
    service = AnalysisService(session, FakeLLMProvider())
    assert service.run() == 36
    assert service.run() == 0
    assert len(DraftService(session, mail).list_pending()) == 21


def test_analysis_failure_on_one_email_does_not_block_the_rest(session, mail):
    IngestService(session, mail).run()
    assert AnalysisService(session, FailingOnceLLM("demo-004")).run() == 35
    # The failed email stays pending, so the next run retries it.
    assert AnalysisService(session, FakeLLMProvider()).run() == 1


def test_digest_covers_the_latest_day_ordered_by_priority(analysed_session):
    digest = DigestService(analysed_session).build()
    assert digest.day == date(2026, 10, 26)
    assert digest.total == 8
    assert digest.counts == {
        Category.URGENT: 2,
        Category.NEEDS_REPLY: 3,
        Category.INFORMATIONAL: 3,
    }
    # Pending drafts count every day, not only the one the digest covers.
    assert digest.pending_drafts == 21
    priorities = [item.analysis.priority for item in digest.items]
    assert priorities == [Priority.HIGH] * 2 + [Priority.MEDIUM] * 3 + [Priority.LOW] * 3
    # Within a priority, the newest email comes first.
    urgent_dates = [item.email.received_at for item in digest.items[:2]]
    assert urgent_dates == sorted(urgent_dates, reverse=True)


def test_digest_items_carry_their_draft(analysed_session):
    for item in DigestService(analysed_session).build().items:
        assert (item.draft is not None) == item.analysis.needs_reply
        if item.draft:
            assert item.draft.email_id == item.email.id
            assert item.draft.status == DraftStatus.PROPOSED


def test_digest_shows_the_decision_taken_on_a_draft(analysed_session, mail):
    drafts = DraftService(analysed_session, mail)
    decided = drafts.list_pending()[0]
    drafts.discard(decided.draft.id)

    digest = DigestService(analysed_session).build()
    shown = next(item for item in digest.items if item.email.id == decided.email.id)
    assert shown.draft.status == DraftStatus.DISCARDED
    assert digest.pending_drafts == 20


def test_digest_can_cover_any_day_and_points_to_its_neighbours(analysed_session):
    service = DigestService(analysed_session)
    latest = service.build()
    assert (latest.previous_day, latest.next_day) == (date(2026, 10, 25), None)

    middle = service.build(date(2026, 10, 24))
    assert middle.day == date(2026, 10, 24)
    assert middle.total == 5
    assert {utc_day(item.email.received_at) for item in middle.items} == {date(2026, 10, 24)}
    assert (middle.previous_day, middle.next_day) == (date(2026, 10, 23), date(2026, 10, 25))
    # Pending drafts count every day, not only the one on screen.
    assert middle.pending_drafts == 21

    oldest = service.build(date(2026, 10, 20))
    assert (oldest.previous_day, oldest.next_day) == (None, date(2026, 10, 21))


def test_digest_of_a_day_without_mail_is_empty_but_points_to_the_days_with_mail(analysed_session):
    digest = DigestService(analysed_session).build(date(2026, 1, 1))
    assert digest.day == date(2026, 1, 1)
    assert digest.total == 0
    assert digest.items == []
    assert (digest.previous_day, digest.next_day) == (None, date(2026, 10, 20))


def test_digest_is_empty_without_mail(session):
    digest = DigestService(session).build()
    assert digest.day is None
    assert (digest.previous_day, digest.next_day) == (None, None)
    assert digest.total == 0
    assert digest.items == []


def test_pending_drafts_come_with_their_email_and_analysis_most_urgent_first(
    analysed_session, mail
):
    pending = DraftService(analysed_session, mail).list_pending()
    assert len(pending) == 21
    assert all(item.draft.status == DraftStatus.PROPOSED for item in pending)
    assert all(item.draft.email_id == item.email.id for item in pending)
    assert pending[0].analysis.priority == Priority.HIGH
    assert pending[-1].analysis.priority == Priority.MEDIUM


def test_metrics_cover_the_seven_days_that_end_on_the_newest_email(analysed_session):
    metrics = MetricsService(analysed_session).build()
    assert [day.day for day in metrics.days] == [
        date(2026, 10, 20) + timedelta(days=offset) for offset in range(7)
    ]
    assert [day.emails for day in metrics.days] == [4, 5, 6, 4, 5, 4, 8]
    assert metrics.emails_processed == 36
    assert metrics.drafts_created == 21
    assert metrics.waiting_for_review == 21
    assert metrics.minutes_saved == 36 * MINUTES_PER_EMAIL + 21 * MINUTES_PER_DRAFT


def test_metrics_waiting_count_drops_when_a_draft_is_decided(analysed_session, mail):
    drafts = DraftService(analysed_session, mail)
    drafts.discard(drafts.list_pending()[0].draft.id)
    metrics = MetricsService(analysed_session).build()
    assert metrics.waiting_for_review == 20
    assert metrics.drafts_created == 21


def test_metrics_ignore_mail_older_than_seven_days(analysed_session):
    old = Email(
        id="old-1",
        sender="Old Sender <old@example.com>",
        subject="Old news",
        body="Nothing new here.",
        received_at=DEMO_NOW - timedelta(days=10),
    )
    EmailRepository(analysed_session).add_if_new(old)
    AnalysisService(analysed_session, FakeLLMProvider()).run()
    assert MetricsService(analysed_session).build().emails_processed == 36


def test_metrics_are_zero_without_mail(session):
    metrics = MetricsService(session).build()
    assert metrics.days == []
    assert metrics.emails_processed == 0
    assert metrics.minutes_saved == 0


def test_a_failed_run_does_not_block_the_next_one(session, mail):
    class BrokenMail(DemoMailProvider):
        def fetch_new(self):
            raise RuntimeError("mailbox unavailable")

    ingest = IngestService(session, BrokenMail(now=DEMO_NOW))
    broken = PipelineService(ingest, AnalysisService(session, FakeLLMProvider()))
    with pytest.raises(RuntimeError):
        broken.run()

    working = PipelineService(
        IngestService(session, mail), AnalysisService(session, FakeLLMProvider())
    )
    assert working.run() == PipelineResult(new_emails=36, analysed=36)


def test_demo_run_loads_the_emails_once(session, mail):
    service = make_demo_service(session, mail)
    assert service.run() == PipelineResult(new_emails=36, analysed=36)
    assert service.run() == PipelineResult(new_emails=0, analysed=0)


def test_demo_reset_deletes_everything_and_loads_the_emails_again(analysed_session, mail):
    drafts = DraftService(analysed_session, mail)
    drafts.discard(drafts.list_pending()[0].draft.id)

    result = make_demo_service(analysed_session, mail).reset()

    assert result == PipelineResult(new_emails=36, analysed=36)
    assert len(drafts.list_pending()) == 21


def test_demo_run_reloads_when_the_stored_emails_are_from_an_earlier_day(session):
    make_demo_service(session, DemoMailProvider(now=DEMO_NOW - timedelta(days=1))).run()

    result = make_demo_service(session, DemoMailProvider(now=DEMO_NOW)).run()

    assert result == PipelineResult(new_emails=36, analysed=36)
    assert DigestService(session).build().day == date(2026, 10, 26)


def test_approve_creates_the_draft_in_the_mailbox(analysed_session, mail):
    service = DraftService(analysed_session, mail)
    draft = service.list_pending()[0].draft
    approved = service.approve(draft.id)
    assert approved.status == DraftStatus.APPROVED
    assert approved.gmail_draft_id == "demo-draft-1"
    assert mail.created_drafts == {"demo-draft-1": draft.body}
    assert len(service.list_pending()) == 20


def test_edited_text_is_what_gets_approved(analysed_session, mail):
    service = DraftService(analysed_session, mail)
    draft = service.list_pending()[0].draft
    service.edit(draft.id, "My own wording.")
    service.approve(draft.id)
    assert list(mail.created_drafts.values()) == ["My own wording."]


def test_discard_does_not_touch_the_mailbox(analysed_session, mail):
    service = DraftService(analysed_session, mail)
    draft = service.list_pending()[0].draft
    assert service.discard(draft.id).status == DraftStatus.DISCARDED
    assert mail.created_drafts == {}


def test_a_discarded_draft_can_be_restored_with_its_text(analysed_session, mail):
    service = DraftService(analysed_session, mail)
    draft = service.list_pending()[0].draft
    service.edit(draft.id, "My own wording.")
    service.discard(draft.id)
    assert len(service.list_pending()) == 20

    restored = service.restore(draft.id)

    assert restored.status == DraftStatus.PROPOSED
    assert restored.body == "My own wording."
    assert len(service.list_pending()) == 21
    # Restoring is not approving: nothing reached the mailbox.
    assert mail.created_drafts == {}


def test_only_a_discarded_draft_can_be_restored(analysed_session, mail):
    service = DraftService(analysed_session, mail)
    pending_id, approved_id = [item.draft.id for item in service.list_pending()[:2]]
    service.approve(approved_id)
    # One is still pending and one is approved (it already exists in the mailbox).
    for draft_id in (pending_id, approved_id):
        with pytest.raises(DraftNotDiscardedError):
            service.restore(draft_id)
    with pytest.raises(DraftNotFoundError):
        service.restore(9999)


def test_a_decided_draft_cannot_change_again(analysed_session, mail):
    service = DraftService(analysed_session, mail)
    draft_id = service.list_pending()[0].draft.id
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
        service.edit(service.list_pending()[0].draft.id, "   ")


def test_factory_builds_demo_providers_in_demo_mode():
    settings = make_settings(demo_mode=True)
    assert isinstance(build_mail_provider(settings), DemoMailProvider)
    assert isinstance(build_llm_provider(settings), FakeLLMProvider)


GOOGLE = {
    "google_client_id": "client-id",
    "google_client_secret": "client-secret",
    "google_refresh_token": "refresh-token",
}


def test_factory_builds_gmail_outside_demo_mode(monkeypatch):
    # The real client is replaced, so the test needs no network and no credentials.
    monkeypatch.setattr("app.factory.build_gmail_service", lambda settings: object())
    provider = build_mail_provider(make_settings(demo_mode=False, **GOOGLE))
    assert isinstance(provider, GmailMailProvider)


def test_factory_explains_what_is_missing_for_gmail():
    with pytest.raises(RuntimeError, match="authorize-gmail"):
        build_mail_provider(make_settings(demo_mode=False))


def test_factory_builds_the_gmail_client_from_the_settings():
    # Building the client does not call Google: the token is only requested on the first use.
    provider = build_mail_provider(make_settings(demo_mode=False, **GOOGLE))
    assert isinstance(provider, GmailMailProvider)


def test_fake_model_can_be_chosen_with_a_real_mailbox():
    settings = make_settings(demo_mode=False, llm_provider="fake")
    assert isinstance(build_llm_provider(settings), FakeLLMProvider)


def test_factory_builds_the_openrouter_model_when_asked(monkeypatch):
    # The real client is replaced, so the test needs no network and no key.
    monkeypatch.setattr("app.factory.build_openrouter_model", lambda settings: object())
    settings = make_settings(demo_mode=False, llm_provider="openrouter")
    assert isinstance(build_llm_provider(settings), LangChainLLMProvider)


def test_demo_mode_keeps_the_fake_model_even_if_openrouter_is_chosen():
    settings = make_settings(demo_mode=True, llm_provider="openrouter")
    assert isinstance(build_llm_provider(settings), FakeLLMProvider)


def test_factory_rejects_an_unknown_model_provider():
    settings = make_settings(demo_mode=False, llm_provider="anthropic")
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        build_llm_provider(settings)
