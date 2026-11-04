"""TC-201 / TC-202: grounded plan proposals, validation, clarifications, edits, G1."""

import json
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient

from gatp.api.services import Services
from gatp.llm_gateway.gateway import LLMGateway, offline_answer
from gatp.llm_gateway.providers import FakeProvider, ProviderRequest
from gatp.store.llm_calls import LlmCallRepository

from .test_api_core import make_project
from .test_api_gates import approve, save_scope


def page_data(req: ProviderRequest) -> dict[str, Any]:
    body = re.search(r"<untrusted_page_data>\n(.*)\n</untrusted_page_data>", req.user, re.S)
    assert body is not None
    data: dict[str, Any] = json.loads(body.group(1))
    return data


def add_book_plan(req: ProviderRequest) -> str:
    """A plausible model answer citing real ids from what it was sent."""
    data = page_data(req)
    by_name = {e["name"]: e["id"] for e in data["elements"] if e["name"]}
    alert = next(
        e["id"] for e in data["elements"] if e.get("attributes", {}).get("id") == "title-error"
    )
    url = data["pages"][0]["url"]
    return json.dumps(
        {
            "cases": [
                {
                    "id": "TC-01",
                    "title": "Title is required",
                    "priority": "high",
                    "steps": [
                        {"action": "goto", "value": url},
                        {
                            "action": "fill",
                            "element_id": by_name["Author"],
                            "value": "Frank Herbert",
                        },
                        {"action": "click", "element_id": by_name["Save"]},
                    ],
                    "expected": [
                        {
                            "kind": "text_equals",
                            "element_id": alert,
                            "value": "Title is required.",
                            "basis": "requirement",
                            "evidence": "FX-5: Title required",
                        },
                        {
                            "kind": "url_contains",
                            "value": "add.html",
                            "basis": "assumption",
                            "evidence": "assumed the page does not change on error",
                        },
                    ],
                    "open_questions": ["Is whitespace-only title also rejected?"],
                }
            ]
        }
    )


@pytest.fixture
def fake(services: Services) -> FakeProvider:
    provider = FakeProvider(name="fake", default=add_book_plan)
    services.__dict__["llm"] = LLMGateway(
        [provider], LlmCallRepository(services.db), sleep=lambda _s: None
    )
    return provider


LOGIN = [
    {"action": "goto", "url": "{base}/index.html"},
    {"action": "fill", "locator": {"strategy": "label", "value": "Username"}, "value": "tester"},
    {"action": "fill", "locator": {"strategy": "label", "value": "Password"}, "value": "secret123"},
    {"action": "click", "locator": {"strategy": "test_id", "value": "login-submit"}},
]


@pytest.fixture
def scoped(client: TestClient, site_v1: str) -> dict[str, Any]:
    pid = make_project(client, site_v1)["id"]
    page = client.post(f"/api/projects/{pid}/pages", json={"url": f"{site_v1}/add.html"}).json()
    steps = json.loads(json.dumps(LOGIN).replace("{base}", site_v1))
    client.put(f"/api/pages/{page['id']}/setup", json={"steps": steps})
    snap = client.post(f"/api/pages/{page['id']}/inspections", json={}).json()["snapshot"]
    scope = save_scope(client, pid, snap["id"])
    approve(client, pid, "G0", scope.json()["version"]["id"])
    return {"pid": pid, "snap": snap}


def test_plan_requires_approved_scope(client: TestClient, site_v1: str, fake: FakeProvider) -> None:
    pid = make_project(client, site_v1)["id"]
    assert client.post(f"/api/projects/{pid}/plan/propose", json={}).status_code == 409
    assert fake.requests == []


def test_proposal_is_grounded_and_raises_clarifications(
    client: TestClient, scoped: dict[str, Any], fake: FakeProvider
) -> None:
    pid = scoped["pid"]
    resp = client.post(f"/api/projects/{pid}/plan/propose", json={})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["version"]["number"] == 1
    assert body["version"]["author"] == "model"
    case = body["plan"]["cases"][0]
    ids = [e["id"] for e in case["expected"]]
    assert ids == ["TC-01.x1", "TC-01.x2"]  # stable ids assigned by GATP
    assert body["validation_errors"] == []
    kinds = sorted(c["kind"] for c in body["open_clarifications"])
    assert kinds == ["assumption", "question"]  # REQ-Q2: assumption + open question asked
    assert any("unconfirmed assumption" in b for b in body["blockers"])
    steps = {s["step"]: s["status"] for s in client.get(f"/api/projects/{pid}/workflow").json()}
    assert steps["plan"] == "blocked"


def test_g1_needs_confirmed_assumptions_and_answers(
    client: TestClient, scoped: dict[str, Any], fake: FakeProvider
) -> None:
    pid = scoped["pid"]
    plan = client.post(f"/api/projects/{pid}/plan/propose", json={}).json()
    v1 = plan["version"]["id"]
    assert approve(client, pid, "G1", v1).status_code == 409
    clar = {c["kind"]: c for c in plan["open_clarifications"]}
    confirm = client.post(
        f"/api/clarifications/{clar['assumption']['id']}/answer",
        json={"answer": "Confirm", "actor": "Abdo"},
    )
    assert confirm.status_code == 200
    client.post(
        f"/api/clarifications/{clar['question']['id']}/answer",
        json={"answer": "Yes, whitespace is rejected", "actor": "Abdo"},
    )
    after = client.get(f"/api/projects/{pid}/plan").json()
    assert after["version"]["number"] == 2  # the confirmation is a new version
    assert after["plan"]["cases"][0]["expected"][1]["confirmed"] is True
    assert after["blockers"] == []
    assert approve(client, pid, "G1", v1).status_code == 409  # old version: not latest
    assert approve(client, pid, "G1", after["version"]["id"]).status_code == 201
    steps = {s["step"]: s["status"] for s in client.get(f"/api/projects/{pid}/workflow").json()}
    assert steps["plan"] == "approved"


def test_answer_with_corrected_value_and_remove(
    client: TestClient, scoped: dict[str, Any], fake: FakeProvider
) -> None:
    pid = scoped["pid"]
    plan = client.post(f"/api/projects/{pid}/plan/propose", json={}).json()
    clar = next(c for c in plan["open_clarifications"] if c["kind"] == "assumption")
    client.post(
        f"/api/clarifications/{clar['id']}/answer",
        json={"answer": "add.html?error", "actor": "Abdo"},
    )
    exp = client.get(f"/api/projects/{pid}/plan").json()["plan"]["cases"][0]["expected"][1]
    assert (exp["value"], exp["basis"], exp["confirmed"]) == ("add.html?error", "requirement", True)
    assert "Abdo" in exp["evidence"]


def test_edit_creates_version_invalidates_g1_and_is_validated(
    client: TestClient, scoped: dict[str, Any], fake: FakeProvider
) -> None:
    pid = scoped["pid"]
    plan = client.post(f"/api/projects/{pid}/plan/propose", json={}).json()
    for c in plan["open_clarifications"]:
        answer = "Confirm" if c["kind"] == "assumption" else "ok"
        client.post(f"/api/clarifications/{c['id']}/answer", json={"answer": answer, "actor": "A"})
    current = client.get(f"/api/projects/{pid}/plan").json()
    assert approve(client, pid, "G1", current["version"]["id"]).status_code == 201
    edited = current["plan"]
    edited["cases"][0]["title"] = "Title is mandatory"
    resp = client.put(
        f"/api/projects/{pid}/plan", json={"plan": edited, "reason": "rename", "actor": "Abdo"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["version"]["author"] == "user"
    assert resp.json()["approved"] is False  # edit after approval -> re-approval needed
    bad = json.loads(json.dumps(edited))
    bad["cases"][0]["steps"][1]["element_id"] = "s999.e1"
    rejected = client.put(f"/api/projects/{pid}/plan", json={"plan": bad, "reason": "x"})
    assert rejected.status_code == 422
    assert "unknown element id" in rejected.json()["detail"]


def test_model_cannot_act_on_regions_or_invent_ids(
    client: TestClient, scoped: dict[str, Any], fake: FakeProvider
) -> None:
    pid = scoped["pid"]
    sid = scoped["snap"]["id"]

    def bad(req: ProviderRequest) -> str:
        plan = json.loads(add_book_plan(req))
        plan["cases"][0]["steps"][1] = {"action": "fill", "element_id": f"s{sid}.o1", "value": "x"}
        return json.dumps(plan)

    fake.default = bad
    resp = client.post(f"/api/projects/{pid}/plan/propose", json={})
    assert resp.status_code == 502  # repair retry also failed -> nothing stored
    assert client.get(f"/api/projects/{pid}/plan").json() is None
    errors = [c["error"] for c in client.get(f"/api/projects/{pid}/llm-calls").json()]
    assert all("is a region, not an interactive element" in e for e in errors)


def test_offline_example_plan_is_valid(
    client: TestClient, scoped: dict[str, Any], services: Services
) -> None:
    services.__dict__["llm"] = LLMGateway(
        [FakeProvider(name="fake", default=offline_answer)], LlmCallRepository(services.db)
    )
    resp = client.post(f"/api/projects/{scoped['pid']}/plan/propose", json={})
    assert resp.status_code == 201, resp.text
    assert resp.json()["validation_errors"] == []
    assert "Offline example" in resp.json()["plan"]["notes"]
