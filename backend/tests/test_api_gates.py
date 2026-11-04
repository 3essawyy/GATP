"""TC-109 (gates) and TC-110 (stored part): approvals bound to versions, clarifications."""

import asyncio
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from gatp.api.events import EventBus
from gatp.api.services import Services

from .test_api_core import make_project


@pytest.fixture
def inspected(client: TestClient, site_v1: str) -> dict[str, Any]:
    pid = make_project(client, site_v1)["id"]
    page = client.get(f"/api/projects/{pid}/pages").json()[0]
    snap = client.post(f"/api/pages/{page['id']}/inspections", json={}).json()["snapshot"]
    return {"pid": pid, "snap": snap}


def save_scope(client: TestClient, pid: int, sid: int, **kw: Any) -> Any:
    body = {"pages": [{"snapshot_id": sid, **kw}], "goal": "Sign in", "actor": "Abdo"}
    return client.put(f"/api/projects/{pid}/scope", json=body)


def step(client: TestClient, pid: int, name: str) -> dict[str, Any]:
    steps: dict[str, dict[str, Any]] = {
        s["step"]: s for s in client.get(f"/api/projects/{pid}/workflow").json()
    }
    return steps[name]


def approve(client: TestClient, pid: int, gate: str, version_id: int | None) -> Any:
    return client.post(
        f"/api/projects/{pid}/approvals",
        json={"gate": gate, "actor": "Abdo", "artifact_version_id": version_id},
    )


def test_scope_selection_is_stored_and_versioned(
    client: TestClient, inspected: dict[str, Any]
) -> None:
    pid, sid = inspected["pid"], inspected["snap"]["id"]
    assert step(client, pid, "inspect")["status"] == "approved"
    assert step(client, pid, "scope")["status"] == "todo"
    first = save_scope(client, pid, sid, include=["e1", "e2", "e3"], exclude=["e2"])
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["version"]["number"] == 1
    assert body["scope"]["pages"][0]["exclude"] == ["e2"]
    assert client.get(f"/api/projects/{pid}").json()["goal"] == "Sign in"
    same = save_scope(client, pid, sid, include=["e1", "e2", "e3"], exclude=["e2"])
    assert same.json()["version"]["number"] == 1  # unchanged content: no new version
    bad = save_scope(client, pid, sid, include=["e99"])
    assert bad.status_code == 422
    assert "e99" in bad.json()["detail"]


def test_gate_requires_exact_version_and_edit_invalidates(
    client: TestClient, inspected: dict[str, Any]
) -> None:
    pid, sid = inspected["pid"], inspected["snap"]["id"]
    v1 = save_scope(client, pid, sid).json()["version"]
    assert step(client, pid, "scope")["status"] == "needs_approval"
    assert approve(client, pid, "G0", None).status_code == 409  # must name a version
    assert approve(client, pid, "G1", v1["id"]).status_code == 409  # wrong gate for a scope
    assert approve(client, pid, "G0", v1["id"]).status_code == 201
    assert step(client, pid, "scope")["status"] == "approved"
    assert client.get(f"/api/projects/{pid}/scope").json()["approved"] is True
    # Editing creates v2, which is not approved: the gate closes again.
    v2 = save_scope(client, pid, sid, exclude=["e1"]).json()
    assert v2["version"]["number"] == 2
    assert v2["approved"] is False
    assert step(client, pid, "scope")["status"] == "needs_approval"
    # The old version can no longer be approved (it is not the latest).
    stale = approve(client, pid, "G0", v1["id"])
    assert stale.status_code == 409
    assert "latest" in stale.json()["detail"]


def test_open_clarification_blocks_step(
    client: TestClient, inspected: dict[str, Any], services: Services
) -> None:
    pid, sid = inspected["pid"], inspected["snap"]["id"]
    v1 = save_scope(client, pid, sid).json()["version"]
    cq = services.gates.raise_clarification(
        pid, "scope", "ambiguous_goal", "Which sign-in outcome matters?", options=["a", "b"]
    )
    assert step(client, pid, "scope")["status"] == "blocked"
    blocked = approve(client, pid, "G0", v1["id"])
    assert blocked.status_code == 409
    assert "clarification" in blocked.json()["detail"]
    listed = client.get(f"/api/projects/{pid}/clarifications", params={"status": "open"}).json()
    assert [c["id"] for c in listed] == [cq.id]
    answer = {"answer": "a", "actor": "Abdo"}
    answered = client.post(f"/api/clarifications/{cq.id}/answer", json=answer)
    assert answered.json()["status"] == "answered"
    assert approve(client, pid, "G0", v1["id"]).status_code == 201
    assert client.post(f"/api/clarifications/{cq.id}/answer", json=answer).status_code == 422


def test_open_inspect_clarification_blocks_inspection(
    client: TestClient, inspected: dict[str, Any], services: Services
) -> None:
    pid = inspected["pid"]
    services.gates.raise_clarification(pid, "inspect", "non_unique", "Which Delete button?")
    page_id = inspected["snap"]["page_id"]
    assert client.post(f"/api/pages/{page_id}/inspections", json={}).status_code == 409


def test_restore_needs_g5_approval_of_that_version(
    client: TestClient, inspected: dict[str, Any]
) -> None:
    pid, sid = inspected["pid"], inspected["snap"]["id"]
    v1 = save_scope(client, pid, sid).json()
    aid = v1["artifact_id"]
    save_scope(client, pid, sid, exclude=["e3"])
    diff = client.get(f"/api/artifacts/{aid}/diff", params={"a": 1, "b": 2}).json()
    assert any(r["tag"] != "equal" for r in diff["rows"])
    no = client.post(f"/api/artifacts/{aid}/restore", json={"number": 1, "approval_id": 999})
    assert no.status_code == 404
    g0 = approve(
        client, pid, "G0", client.get(f"/api/projects/{pid}/scope").json()["version"]["id"]
    )
    wrong = client.post(
        f"/api/artifacts/{aid}/restore", json={"number": 1, "approval_id": g0.json()["id"]}
    )
    assert wrong.status_code == 409
    g5 = approve(client, pid, "G5", v1["version"]["id"]).json()
    restored = client.post(
        f"/api/artifacts/{aid}/restore", json={"number": 1, "approval_id": g5["id"]}
    )
    assert restored.status_code == 201
    assert restored.json()["number"] == 3
    assert restored.json()["author"] == "restore"
    assert [v["number"] for v in client.get(f"/api/artifacts/{aid}/versions").json()] == [1, 2, 3]


def test_user_edit_creates_new_version(client: TestClient, inspected: dict[str, Any]) -> None:
    pid, sid = inspected["pid"], inspected["snap"]["id"]
    aid = save_scope(client, pid, sid).json()["artifact_id"]
    edit = client.post(
        f"/api/artifacts/{aid}/versions",
        json={"content": '{"pages": []}', "reason": "manual", "actor": "Abdo"},
    )
    assert edit.status_code == 201
    assert edit.json()["author"] == "user"
    kinds = client.get(f"/api/projects/{pid}/artifacts", params={"kind": "scope"}).json()
    assert len(kinds) == 1


def test_event_bus_delivers_to_subscribers() -> None:
    async def scenario() -> list[str]:
        bus = EventBus()
        bus.bind(asyncio.get_running_loop())
        stream = bus.stream(7, heartbeat_s=5)
        received = [await anext(stream)]
        reader = asyncio.ensure_future(anext(stream))
        await asyncio.sleep(0)
        bus.publish(7, "approved", {"gate": "G0"})
        bus.publish(8, "other")  # different project: not delivered
        received.append(await asyncio.wait_for(reader, 2))
        await stream.aclose()
        return received

    first, second = asyncio.run(scenario())
    assert first == ": connected\n\n"
    assert second.startswith("event: approved\n")
    payload = json.loads(second.split("data: ", 1)[1])
    assert payload == {"type": "approved", "project_id": 7, "data": {"gate": "G0"}}
