"""TC-205 / TC-206: approved execution (G3), results, real failures stay visible."""

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from gatp.llm_gateway.providers import FakeProvider, ProviderRequest

from .test_api_plan import add_book_plan, fake, scoped  # noqa: F401 - fixtures
from .test_codegen import plan_approved


def code_approved(client: TestClient, pid: int) -> None:
    plan_approved(client, pid)
    client.post(f"/api/projects/{pid}/code/generate")
    assert client.post(f"/api/projects/{pid}/code/validate").json()["report"]["ok"]
    assert client.post(f"/api/projects/{pid}/code/approve", json={"actor": "A"}).status_code == 201


def approve_run(client: TestClient, pid: int) -> int:
    subject = client.get(f"/api/projects/{pid}/runs/subject").json()["subject"]
    resp = client.post(
        f"/api/projects/{pid}/approvals", json={"gate": "G3", "actor": "Abdo", "subject": subject}
    )
    assert resp.status_code == 201, resp.text
    approval_id: int = resp.json()["id"]
    return approval_id


@pytest.mark.usefixtures("fake")
def test_run_requires_matching_single_use_g3(client: TestClient, scoped: dict[str, Any]) -> None:  # noqa: F811
    pid = scoped["pid"]
    code_approved(client, pid)
    g2 = client.get(f"/api/projects/{pid}/approvals").json()[-1]["id"]
    assert client.post(f"/api/projects/{pid}/runs", json={"approval_id": g2}).status_code == 409
    wrong = {"code_version_ids": [1], "target": "http://evil.test", "tests": []}
    bad = client.post(
        f"/api/projects/{pid}/approvals", json={"gate": "G3", "actor": "A", "subject": wrong}
    )
    assert bad.status_code == 409  # G3 must name exactly the current code + target

    approval = approve_run(client, pid)
    run = client.post(f"/api/projects/{pid}/runs", json={"approval_id": approval})
    assert run.status_code == 201, run.text
    body = run.json()
    assert body["status"] == "passed", body
    [result] = body["results"]
    assert result["outcome"] == "passed"
    assert result["test_id"].endswith("test_tc_01_title_is_required[chromium]")
    assert result["screenshot_path"].endswith(".png")
    assert body["duration_ms"] > 0  # execution time, separate from model time
    assert body["scope"]["isolation"] in ("bwrap", "process")
    shot = client.get(f"/api/files/{result['screenshot_path']}")
    assert shot.content[:4] == b"\x89PNG"
    again = client.post(f"/api/projects/{pid}/runs", json={"approval_id": approval})
    assert again.status_code == 422  # one approval, one run
    steps = {s["step"]: s["status"] for s in client.get(f"/api/projects/{pid}/workflow").json()}
    assert steps["run"] == "approved"


@pytest.mark.usefixtures("fake")
def test_code_edit_after_g3_invalidates_the_run_approval(
    client: TestClient,
    scoped: dict[str, Any],  # noqa: F811
) -> None:
    pid = scoped["pid"]
    code_approved(client, pid)
    approval = approve_run(client, pid)
    files = client.get(f"/api/projects/{pid}/code").json()["files"]
    test_file = next(f for f in files if f["path"] == "tests/test_plan.py")
    client.post(
        f"/api/artifacts/{test_file['artifact_id']}/versions",
        json={"content": test_file["version"]["content"] + "\n", "reason": "x", "actor": "A"},
    )
    refused = client.post(f"/api/projects/{pid}/runs", json={"approval_id": approval})
    assert refused.status_code == 409


def test_real_failure_stays_visible(
    client: TestClient,
    scoped: dict[str, Any],  # noqa: F811
    fake: FakeProvider,  # noqa: F811
) -> None:
    """A case expecting behaviour the site does not have fails with details (TC-206)."""

    def wrong_expectation(req: ProviderRequest) -> str:
        plan = json.loads(add_book_plan(req))
        plan["cases"][0]["expected"][0]["value"] = "Please enter a title"  # not what the site says
        return json.dumps(plan)

    fake.default = wrong_expectation
    pid = scoped["pid"]
    code_approved(client, pid)
    run = client.post(
        f"/api/projects/{pid}/runs", json={"approval_id": approve_run(client, pid)}
    ).json()
    assert run["status"] == "failed"
    [result] = run["results"]
    assert result["outcome"] == "failed"
    assert "Please enter a title" in result["message"]
    assert "Title is required." in result["message"] + result["details"]  # actual value shown
    assert result["screenshot_path"].endswith("test-failed-1.png")
    code = client.get(f"/api/projects/{pid}/code").json()["files"]
    tests = next(f for f in code if f["path"] == "tests/test_plan.py")["version"]
    assert tests["number"] == 1  # nothing rewrote the assertion to make it pass
    steps = {s["step"]: s for s in client.get(f"/api/projects/{pid}/workflow").json()}
    assert steps["run"]["status"] == "failed"
    assert "0/1 passed" in steps["run"]["detail"]
