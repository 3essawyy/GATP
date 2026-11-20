"""T-008: projects, pages, inspections through the runner, files, errors."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from .conftest import InProcessRunner


def make_project(client: TestClient, base: str) -> dict[str, Any]:
    resp = client.post("/api/projects", json={"name": "BookShelf", "url": f"{base}/index.html"})
    assert resp.status_code == 201, resp.text
    project: dict[str, Any] = resp.json()
    return project


def test_create_project_adds_start_page_and_origin(client: TestClient, site_v1: str) -> None:
    project = make_project(client, site_v1)
    assert project["origin"] == site_v1
    pages = client.get(f"/api/projects/{project['id']}/pages").json()
    assert [p["url"] for p in pages] == [f"{site_v1}/index.html"]
    assert client.get("/api/projects").json()[0]["id"] == project["id"]


def test_pages_must_stay_on_origin(client: TestClient, site_v1: str) -> None:
    pid = make_project(client, site_v1)["id"]
    ok = client.post(f"/api/projects/{pid}/pages", json={"url": f"{site_v1}/add.html"})
    assert ok.status_code == 201
    bad = client.post(f"/api/projects/{pid}/pages", json={"url": "http://evil.test/x"})
    assert bad.status_code == 422
    assert bad.json()["error"] == "invalid"


def test_goal_and_requirements(client: TestClient, site_v1: str) -> None:
    pid = make_project(client, site_v1)["id"]
    goal = client.put(f"/api/projects/{pid}/goal", json={"goal": "Sign-in works"}).json()
    assert goal["goal"] == "Sign-in works"
    client.post(f"/api/projects/{pid}/requirements", json={"text": "Wrong password shows error"})
    reqs = client.get(f"/api/projects/{pid}/requirements").json()
    assert [r["text"] for r in reqs] == ["Wrong password shows error"]


def test_not_found_is_404_json(client: TestClient) -> None:
    resp = client.get("/api/projects/999")
    assert resp.status_code == 404
    assert resp.json() == {"error": "not_found", "detail": "project 999"}


def test_inspect_page_stores_snapshot_and_files(
    client: TestClient, site_v1: str, runner: InProcessRunner
) -> None:
    pid = make_project(client, site_v1)["id"]
    page = client.get(f"/api/projects/{pid}/pages").json()[0]
    resp = client.post(f"/api/pages/{page['id']}/inspections", json={})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    snap = body["snapshot"]
    names = [e["name"] for e in snap["elements"] if e["details"]["interactive"]]
    assert names == ["Username", "Password", "Sign in"]
    assert [e["key"] for e in snap["elements"] if not e["details"]["interactive"]] == ["o1", "o2"]
    assert snap["elements"][2]["locators"][0]["unique"] is True
    assert body["duration_ms"] > 0
    assert runner.jobs[0].allowlist == [site_v1]  # the project origin is the allowlist
    listed = client.get(f"/api/pages/{page['id']}/snapshots").json()
    assert listed[0]["id"] == snap["id"]
    assert listed[0]["element_count"] == 5  # 3 interactive + 2 observable
    shot = client.get(f"/api/files/{snap['screenshot_path']}")
    assert shot.status_code == 200
    assert shot.content.startswith(b"\x89PNG")
    assert client.get("/api/files/../../etc/passwd").status_code in (404, 422)


def test_inspect_uses_page_setup_steps(client: TestClient, site_v1: str) -> None:
    pid = make_project(client, site_v1)["id"]
    page = client.post(f"/api/projects/{pid}/pages", json={"url": f"{site_v1}/add.html"}).json()
    steps = [
        {"action": "goto", "url": f"{site_v1}/index.html"},
        {
            "action": "fill",
            "locator": {"strategy": "label", "value": "Username"},
            "value": "tester",
        },
        {
            "action": "fill",
            "locator": {"strategy": "label", "value": "Password"},
            "value": "secret123",
        },
        {"action": "click", "locator": {"strategy": "test_id", "value": "login-submit"}},
    ]
    saved = client.put(f"/api/pages/{page['id']}/setup", json={"steps": steps})
    assert saved.status_code == 200, saved.text
    assert len(saved.json()["setup"]) == 4
    snap = client.post(f"/api/pages/{page['id']}/inspections", json={}).json()["snapshot"]
    assert snap["title"] == "BookShelf · Add book"
    off = [{"action": "goto", "url": "http://evil.test/"}]
    assert client.put(f"/api/pages/{page['id']}/setup", json={"steps": off}).status_code == 422


@pytest.mark.parametrize(
    "bad", ["index.html", "/index.html", "ftp://host/x", "javascript:alert(1)"]
)
def test_setup_goto_not_a_full_http_url_is_422(client: TestClient, site_v1: str, bad: str) -> None:
    pid = make_project(client, site_v1)["id"]
    page = client.post(f"/api/projects/{pid}/pages", json={"url": f"{site_v1}/add.html"}).json()
    steps = [{"action": "goto", "url": bad}]
    res = client.put(f"/api/pages/{page['id']}/setup", json={"steps": steps})
    assert res.status_code == 422, res.text
    assert "full http(s) URL" in res.text


def test_runner_down_is_503(client: TestClient, site_v1: str, runner: InProcessRunner) -> None:
    pid = make_project(client, site_v1)["id"]
    page = client.get(f"/api/projects/{pid}/pages").json()[0]
    runner.executor = None
    resp = client.post(f"/api/pages/{page['id']}/inspections", json={})
    assert resp.status_code == 503
    assert "poe runner" in resp.json()["detail"]
    assert client.get("/api/runner/health").json()["available"] is False
