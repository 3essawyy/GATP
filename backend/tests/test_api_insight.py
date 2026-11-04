"""TC-111 (automated) / TC-110 (model part): grounded insight call on the approved scope only."""

import json
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient

from gatp.api.services import Services
from gatp.llm_gateway.gateway import LLMGateway
from gatp.llm_gateway.providers import FakeProvider, ProviderRequest
from gatp.store.llm_calls import LlmCallRepository

from .test_api_core import make_project
from .test_api_gates import approve, save_scope


def grounded_answer(request: ProviderRequest) -> str:
    """A fake model that cites only ids present in the page data it was given."""
    ids = re.findall(r'"id": "(s\d+\.e\d+)"', request.user)
    return json.dumps(
        {
            "summary": f"{len(ids)} elements in scope",
            "elements": [{"element_id": i, "observation": "seen"} for i in ids],
            "next_actions": [
                {
                    "action": "Submit with the first field empty",
                    "element_ids": ids[:1],
                    "basis": "assumption",
                    "rationale": "required-field rule not shown on the page",
                }
            ],
            "assumptions": ["Title is required"],
            "questions": ["Which fields are mandatory?"],
        }
    )


@pytest.fixture
def fake_llm(services: Services) -> FakeProvider:
    fake = FakeProvider(name="fake", default=grounded_answer)
    services.__dict__["llm"] = LLMGateway(
        [fake], LlmCallRepository(services.db), sleep=lambda _s: None
    )
    return fake


@pytest.fixture
def approved(client: TestClient, site_v1: str) -> dict[str, Any]:
    pid = make_project(client, site_v1)["id"]
    page = client.get(f"/api/projects/{pid}/pages").json()[0]
    snap = client.post(f"/api/pages/{page['id']}/inspections", json={}).json()["snapshot"]
    scope = save_scope(client, pid, snap["id"], exclude=["e2"]).json()
    return {"pid": pid, "snap": snap, "scope": scope}


def test_insight_requires_approved_scope(
    client: TestClient, site_v1: str, fake_llm: FakeProvider
) -> None:
    pid = make_project(client, site_v1)["id"]
    resp = client.post(f"/api/projects/{pid}/insight")
    assert resp.status_code == 409
    page = client.get(f"/api/projects/{pid}/pages").json()[0]
    snap = client.post(f"/api/pages/{page['id']}/inspections", json={}).json()["snapshot"]
    save_scope(client, pid, snap["id"])
    blocked = client.post(f"/api/projects/{pid}/insight")
    assert blocked.status_code == 409
    assert "G0" in blocked.json()["detail"]
    assert fake_llm.requests == []  # nothing was sent before approval


def test_only_scoped_elements_are_sent_and_cited(
    client: TestClient, approved: dict[str, Any], fake_llm: FakeProvider
) -> None:
    pid, sid = approved["pid"], approved["snap"]["id"]
    approve(client, pid, "G0", approved["scope"]["version"]["id"])
    resp = client.post(f"/api/projects/{pid}/insight")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # e2 excluded by the tester (TC-110); observables o1 (heading), o2 (alert) stay in scope
    assert body["element_ids_sent"] == [f"s{sid}.e1", f"s{sid}.e3", f"s{sid}.o1", f"s{sid}.o2"]
    sent = fake_llm.requests[0]
    assert f"s{sid}.e2" not in sent.user
    assert '"name": "Password"' not in sent.user  # (it may appear as nearby text of e3)
    assert "<untrusted_page_data>" in sent.user
    assert "Sign in" in sent.user  # goal from the scope (trusted part)
    cited = {n["element_id"] for n in body["insight"]["elements"]}
    assert cited <= set(body["element_ids_sent"])
    call = body["call"]
    assert (call["provider"], call["status"], call["cache"]) == ("fake", "ok", "fresh")
    assert call["tokens_estimated"] is True
    assert call["latency_ms"] >= 0
    assert body["browser_ms"] > 0  # inspection time reported separately (REQ-Q8)
    assert body["insight"]["next_actions"][0]["basis"] == "assumption"
    latest = client.get(f"/api/projects/{pid}/insight").json()
    assert latest["call"]["id"] == call["id"]
    calls = client.get(f"/api/projects/{pid}/llm-calls").json()
    assert calls[0]["request"].startswith("[system]")


def test_second_identical_request_is_reused(
    client: TestClient, approved: dict[str, Any], fake_llm: FakeProvider
) -> None:
    pid = approved["pid"]
    approve(client, pid, "G0", approved["scope"]["version"]["id"])
    client.post(f"/api/projects/{pid}/insight")
    again = client.post(f"/api/projects/{pid}/insight").json()
    assert again["call"]["cache"] == "reused"
    assert len(fake_llm.requests) == 1


def test_invented_element_ids_are_rejected(
    client: TestClient, approved: dict[str, Any], fake_llm: FakeProvider
) -> None:
    pid = approved["pid"]
    approve(client, pid, "G0", approved["scope"]["version"]["id"])
    invented = json.dumps(
        {
            "summary": "x",
            "elements": [{"element_id": "s99.e7", "observation": "made up"}],
            "next_actions": [],
            "assumptions": [],
            "questions": [],
        }
    )
    fake_llm.script = [invented, invented]
    resp = client.post(f"/api/projects/{pid}/insight")
    assert resp.status_code == 502
    assert resp.json()["error"] == "model_output_invalid"
    statuses = [c["status"] for c in client.get(f"/api/projects/{pid}/llm-calls").json()]
    assert statuses == ["invalid_output", "invalid_output"]  # first answer + repair retry
