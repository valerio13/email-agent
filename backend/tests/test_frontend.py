"""The API serves the built dashboard when there is one, and keeps working when there is not."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import serve_frontend


@pytest.fixture
def dist(tmp_path):
    (tmp_path / "index.html").write_text("<html>dashboard</html>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('dashboard')")
    return tmp_path


def make_client(directory) -> TestClient:
    app = FastAPI()

    @app.get("/api/ping")
    def ping() -> dict[str, bool]:
        return {"ok": True}

    serve_frontend(app, directory)
    return TestClient(app)


def test_serves_the_dashboard_and_its_files(dist):
    client = make_client(dist)
    page = client.get("/")
    assert page.status_code == 200
    assert "dashboard" in page.text
    assert client.get("/assets/app.js").status_code == 200


def test_api_routes_win_and_unknown_api_paths_stay_json_errors(dist):
    client = make_client(dist)
    assert client.get("/api/ping").json() == {"ok": True}
    missing = client.get("/api/nothing-here")
    assert missing.status_code == 404
    assert missing.headers["content-type"] == "application/json"


def test_without_a_build_only_the_api_runs(tmp_path):
    client = make_client(tmp_path / "not-built")
    assert client.get("/api/ping").json() == {"ok": True}
    assert client.get("/").status_code == 404
