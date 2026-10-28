"""API tests: real routers and services on an in-memory database, with the demo providers."""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_services
from app.core.config import get_settings
from app.factory import build_services
from app.main import app
from app.providers.llm.fake import FakeLLMProvider
from app.providers.mail.demo import DemoMailProvider
from tests.helpers import DEMO_NOW, make_settings


@pytest.fixture
def mail():
    return DemoMailProvider(now=DEMO_NOW)


@pytest.fixture
def client(session, mail, monkeypatch):
    services = build_services(session, mail, FakeLLMProvider())
    app.dependency_overrides[get_services] = lambda: services
    app.dependency_overrides[get_settings] = lambda: make_settings(demo_mode=True)
    # The app's startup reads the settings directly, so patch that call too (scheduler stays off).
    monkeypatch.setattr("app.main.get_settings", lambda: make_settings(demo_mode=True))
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def loaded_client(client):
    """A client whose database already holds the 36 analysed demo emails."""
    assert client.post("/api/demo/run").status_code == 200
    return client


def test_demo_run_loads_the_emails_once(client):
    first = client.post("/api/demo/run")
    assert first.json() == {"new_emails": 36, "analysed": 36}
    assert client.post("/api/demo/run").json() == {"new_emails": 0, "analysed": 0}


@pytest.mark.parametrize("path", ["/api/demo/run", "/api/demo/reset"])
def test_demo_endpoints_are_forbidden_outside_demo_mode(client, path):
    app.dependency_overrides[get_settings] = lambda: make_settings(demo_mode=False)
    assert client.post(path).status_code == 403


def test_demo_reset_deletes_everything_and_loads_the_emails_again(loaded_client):
    draft_id = loaded_client.get("/api/drafts").json()[0]["draft"]["id"]
    loaded_client.post(f"/api/drafts/{draft_id}/discard")
    assert loaded_client.post("/api/demo/reset").json() == {"new_emails": 36, "analysed": 36}
    assert len(loaded_client.get("/api/drafts").json()) == 21


def test_config_tells_whether_the_app_runs_in_demo_mode(client):
    assert client.get("/api/config").json() == {"demo_mode": True}
    app.dependency_overrides[get_settings] = lambda: make_settings(demo_mode=False)
    assert client.get("/api/config").json() == {"demo_mode": False}


def test_digest_is_empty_before_the_first_run(client):
    digest = client.get("/api/digest").json()
    assert digest["day"] is None
    assert digest["total"] == 0
    assert digest["items"] == []


def test_digest_covers_the_latest_day_by_priority(loaded_client):
    digest = loaded_client.get("/api/digest").json()
    assert digest["day"] == "2026-10-26"
    assert digest["total"] == 8
    assert digest["counts"] == {"urgent": 2, "needs_reply": 3, "informational": 3}
    assert digest["pending_drafts"] == 21
    assert digest["items"][0]["analysis"]["priority"] == "high"
    assert digest["items"][-1]["analysis"]["priority"] == "low"


def test_digest_items_include_the_draft_status(loaded_client):
    draft = loaded_client.get("/api/drafts").json()[0]["draft"]
    loaded_client.post(f"/api/drafts/{draft['id']}/approve")
    items = loaded_client.get("/api/digest").json()["items"]
    shown = next(item for item in items if item["draft"] and item["draft"]["id"] == draft["id"])
    assert shown["draft"]["status"] == "approved"
    assert all(item["draft"] is None for item in items if not item["analysis"]["needs_reply"])


def test_metrics_report_the_week(loaded_client):
    metrics = loaded_client.get("/api/metrics").json()
    assert [day["emails"] for day in metrics["days"]] == [4, 5, 6, 4, 5, 4, 8]
    assert metrics["days"][-1]["day"] == "2026-10-26"
    assert metrics["emails_processed"] == 36
    assert metrics["drafts_created"] == 21
    assert metrics["waiting_for_review"] == 21
    assert metrics["minutes_saved"] == 36 * 2 + 21 * 6


def test_metrics_are_empty_before_the_first_run(client):
    metrics = client.get("/api/metrics").json()
    assert metrics["days"] == []
    assert metrics["emails_processed"] == 0


def test_pending_drafts_come_with_their_email_and_analysis(loaded_client):
    pending = loaded_client.get("/api/drafts").json()
    assert len(pending) == 21
    first = pending[0]
    assert first["draft"]["status"] == "proposed"
    assert first["draft"]["email_id"] == first["email"]["id"]
    assert first["analysis"]["priority"] == "high"


def test_pending_drafts_can_be_edited_and_approved(loaded_client, mail):
    draft_id = loaded_client.get("/api/drafts").json()[0]["draft"]["id"]

    edited = loaded_client.patch(f"/api/drafts/{draft_id}", json={"body": "My wording."})
    assert edited.json()["body"] == "My wording."

    approved = loaded_client.post(f"/api/drafts/{draft_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["gmail_draft_id"] == "demo-draft-1"
    assert list(mail.created_drafts.values()) == ["My wording."]
    assert len(loaded_client.get("/api/drafts").json()) == 20


def test_discarded_draft_leaves_the_pending_list(loaded_client, mail):
    draft_id = loaded_client.get("/api/drafts").json()[0]["draft"]["id"]
    discarded = loaded_client.post(f"/api/drafts/{draft_id}/discard")
    assert discarded.json()["status"] == "discarded"
    assert mail.created_drafts == {}
    assert len(loaded_client.get("/api/drafts").json()) == 20


def test_deciding_twice_returns_conflict(loaded_client):
    draft_id = loaded_client.get("/api/drafts").json()[0]["draft"]["id"]
    loaded_client.post(f"/api/drafts/{draft_id}/approve")
    assert loaded_client.post(f"/api/drafts/{draft_id}/approve").status_code == 409
    assert loaded_client.post(f"/api/drafts/{draft_id}/discard").status_code == 409


def test_unknown_draft_returns_not_found(loaded_client):
    assert loaded_client.post("/api/drafts/9999/approve").status_code == 404


def test_empty_draft_text_is_rejected(loaded_client):
    draft_id = loaded_client.get("/api/drafts").json()[0]["draft"]["id"]
    assert loaded_client.patch(f"/api/drafts/{draft_id}", json={"body": "  "}).status_code == 422
