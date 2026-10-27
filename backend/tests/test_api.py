"""API tests: real routers and services on an in-memory database, with the demo providers."""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_services
from app.core.config import get_settings
from app.factory import build_services
from app.main import app
from app.providers.llm.fake import FakeLLMProvider
from app.providers.mail.demo import DemoMailProvider
from tests.helpers import make_settings


@pytest.fixture
def mail():
    return DemoMailProvider()


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
    """A client whose database already holds the 11 analysed demo emails."""
    assert client.post("/api/demo/run").status_code == 200
    return client


def test_demo_run_loads_the_emails_once(client):
    first = client.post("/api/demo/run")
    assert first.json() == {"new_emails": 11, "analysed": 11}
    assert client.post("/api/demo/run").json() == {"new_emails": 0, "analysed": 0}


def test_demo_run_is_forbidden_outside_demo_mode(client):
    app.dependency_overrides[get_settings] = lambda: make_settings(demo_mode=False)
    assert client.post("/api/demo/run").status_code == 403


def test_digest_is_empty_before_the_first_run(client):
    digest = client.get("/api/digest").json()
    assert digest["total"] == 0
    assert digest["items"] == []


def test_digest_lists_emails_by_priority(loaded_client):
    digest = loaded_client.get("/api/digest").json()
    assert digest["total"] == 11
    assert digest["counts"] == {"urgent": 3, "needs_reply": 4, "informational": 4}
    assert digest["pending_drafts"] == 7
    assert digest["items"][0]["analysis"]["priority"] == "high"
    assert digest["items"][-1]["analysis"]["priority"] == "low"


def test_pending_drafts_can_be_listed_edited_and_approved(loaded_client, mail):
    drafts = loaded_client.get("/api/drafts").json()
    assert len(drafts) == 7
    draft_id = drafts[0]["id"]

    edited = loaded_client.patch(f"/api/drafts/{draft_id}", json={"body": "My wording."})
    assert edited.json()["body"] == "My wording."

    approved = loaded_client.post(f"/api/drafts/{draft_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["gmail_draft_id"] == "demo-draft-1"
    assert list(mail.created_drafts.values()) == ["My wording."]
    assert len(loaded_client.get("/api/drafts").json()) == 6


def test_discarded_draft_leaves_the_pending_list(loaded_client, mail):
    draft_id = loaded_client.get("/api/drafts").json()[0]["id"]
    discarded = loaded_client.post(f"/api/drafts/{draft_id}/discard")
    assert discarded.json()["status"] == "discarded"
    assert mail.created_drafts == {}
    assert len(loaded_client.get("/api/drafts").json()) == 6


def test_deciding_twice_returns_conflict(loaded_client):
    draft_id = loaded_client.get("/api/drafts").json()[0]["id"]
    loaded_client.post(f"/api/drafts/{draft_id}/approve")
    assert loaded_client.post(f"/api/drafts/{draft_id}/approve").status_code == 409
    assert loaded_client.post(f"/api/drafts/{draft_id}/discard").status_code == 409


def test_unknown_draft_returns_not_found(loaded_client):
    assert loaded_client.post("/api/drafts/9999/approve").status_code == 404


def test_empty_draft_text_is_rejected(loaded_client):
    draft_id = loaded_client.get("/api/drafts").json()[0]["id"]
    assert loaded_client.patch(f"/api/drafts/{draft_id}", json={"body": "  "}).status_code == 422
