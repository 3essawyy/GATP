"""TC-207: feedback on a run -> revision -> re-approval -> approved rerun; no silent weakening."""

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from gatp.api.run_service import failed_expectations
from gatp.codegen.guard import code_weakenings
from gatp.llm_gateway.providers import FakeProvider, ProviderRequest
from gatp.test_designer.guard import plan_weakenings, restore
from gatp.test_designer.plan import TestPlan, _offline_revision

from .test_api_plan import add_book_plan, fake, page_data, scoped  # noqa: F401 - fixtures
from .test_codegen import plan_approved
from .test_runs import approve_run, code_approved


def _clars(client: TestClient, pid: int, kind: str = "weakening") -> list[dict[str, Any]]:
    rows = client.get(f"/api/projects/{pid}/clarifications", params={"status": "open"}).json()
    return [c for c in rows if c["kind"] == kind]


def _answer(client: TestClient, clar: dict[str, Any], answer: str) -> Any:
    return client.post(
        f"/api/clarifications/{clar['id']}/answer", json={"answer": answer, "actor": "Abdo"}
    )


def test_feedback_on_failed_run_revises_and_reruns(
    client: TestClient,
    scoped: dict[str, Any],  # noqa: F811
    fake: FakeProvider,  # noqa: F811
) -> None:
    """The demo step: run fails -> feedback -> model revises -> flagged -> G1/G2/G3 -> passes."""
    seen: list[ProviderRequest] = []

    def model(req: ProviderRequest) -> str:
        seen.append(req)
        plan = json.loads(add_book_plan(req))
        if "Current plan:" not in req.user:  # first proposal: a wrong expected text
            plan["cases"][0]["expected"][0]["value"] = "Please enter a title"
        return json.dumps(plan)  # revision: the corrected text the run showed

    fake.default = model
    pid = scoped["pid"]
    code_approved(client, pid)
    run = client.post(f"/api/projects/{pid}/runs", json={"approval_id": approve_run(client, pid)})
    failed = run.json()
    assert failed["status"] == "failed"
    [result] = failed["results"]
    assert result["failed_expectations"] == ["TC-01.x1"]  # failure maps back to the plan

    revised = client.post(
        f"/api/projects/{pid}/plan/propose",
        json={"feedback": "The page says 'Title is required.'", "run_id": failed["id"]},
    )
    assert revised.status_code == 201, revised.text
    body = revised.json()
    assert "from run #" in body["version"]["reason"]
    # The run's failure went to the model as untrusted page data, not as instructions.
    data = page_data(seen[-1])
    assert data["run_results"][0]["failed_expectations"] == ["TC-01.x1"]
    instructions = seen[-1].user.split("<untrusted_page_data>")[0]
    assert result["message"][:60] in data["run_results"][0]["message"]
    assert result["message"][:60] not in instructions

    # The changed check is flagged and blocks G1 until the tester decides explicitly.
    [flag] = _clars(client, pid)
    assert "TC-01.x1 was changed" in flag["question"]
    version_id = body["version"]["id"]
    blocked = client.post(
        f"/api/projects/{pid}/approvals",
        json={"gate": "G1", "actor": "A", "artifact_version_id": version_id},
    )
    assert blocked.status_code == 409
    assert _answer(client, flag, "ok").status_code == 422  # no free-text waving through
    assert _answer(client, flag, "Accept this change").status_code == 200
    ok = client.post(
        f"/api/projects/{pid}/approvals",
        json={"gate": "G1", "actor": "A", "artifact_version_id": version_id},
    )
    assert ok.status_code == 201, ok.text

    # Regenerate -> validate -> G2 -> new G3 -> rerun passes.
    client.post(f"/api/projects/{pid}/code/generate")
    assert client.post(f"/api/projects/{pid}/code/validate").json()["report"]["ok"]
    assert client.post(f"/api/projects/{pid}/code/approve", json={"actor": "A"}).status_code == 201
    rerun = client.post(f"/api/projects/{pid}/runs", json={"approval_id": approve_run(client, pid)})
    assert rerun.json()["status"] == "passed", rerun.text
    assert _clars(client, pid) == []


@pytest.mark.usefixtures("fake")
def test_removed_check_is_flagged_and_can_be_restored(
    client: TestClient,
    scoped: dict[str, Any],  # noqa: F811
) -> None:
    pid = scoped["pid"]
    approved = plan_approved(client, pid)
    plan = approved["plan"]
    plan["cases"][0]["expected"] = plan["cases"][0]["expected"][:1]  # drop TC-01.x2
    edit = client.put(
        f"/api/projects/{pid}/plan", json={"plan": plan, "reason": "too strict", "actor": "B"}
    )
    assert edit.status_code == 200
    [flag] = _clars(client, pid)
    assert flag["question"].startswith("TC-01.x2 was removed")
    _answer(client, flag, "Restore the approved version")
    current = client.get(f"/api/projects/{pid}/plan").json()
    restored = current["plan"]["cases"][0]["expected"]
    assert [e["id"] for e in restored] == ["TC-01.x1", "TC-01.x2"]
    assert restored[1]["confirmed"] is True  # the tester's earlier confirmation is kept
    assert current["blockers"] == []
    assert _clars(client, pid) == []


@pytest.mark.usefixtures("fake")
def test_weakened_test_code_is_flagged_before_g2(
    client: TestClient,
    scoped: dict[str, Any],  # noqa: F811
) -> None:
    pid = scoped["pid"]
    code_approved(client, pid)
    files = client.get(f"/api/projects/{pid}/code").json()["files"]
    tests = next(f for f in files if f["path"] == "tests/test_plan.py")
    approved_content = tests["version"]["content"]
    weakened = "\n".join(
        line for line in approved_content.splitlines() if "to_have_text" not in line
    )
    client.post(
        f"/api/artifacts/{tests['artifact_id']}/versions",
        json={"content": weakened, "reason": "flaky", "actor": "B"},
    )
    [flag] = _clars(client, pid)
    assert flag["step"] == "code"
    assert "assertion removed or changed" in flag["question"]
    client.post(f"/api/projects/{pid}/code/validate")
    blocked = client.post(f"/api/projects/{pid}/code/approve", json={"actor": "A"})
    assert blocked.status_code == 409  # open clarification on step code
    _answer(client, flag, "Restore the approved version")
    latest = client.get(f"/api/projects/{pid}/code").json()["files"]
    content = next(f for f in latest if f["path"] == "tests/test_plan.py")["version"]["content"]
    assert content == approved_content
    assert _clars(client, pid) == []


def test_guard_units() -> None:
    plan = TestPlan.model_validate(
        {
            "cases": [
                {
                    "id": "TC-01",
                    "title": "t",
                    "steps": [{"action": "goto", "value": "http://x/a"}],
                    "expected": [
                        {
                            "id": "TC-01.x1",
                            "kind": "text_equals",
                            "element_id": "s1.o1",
                            "value": "Title is required.",
                            "basis": "requirement",
                            "evidence": "FX-5",
                        }
                    ],
                },
            ]
        }
    )
    looser = plan.model_copy(deep=True)
    looser.cases[0].expected[0].kind = "text_contains"
    [w] = plan_weakenings(plan, looser)
    assert w.change == "loosened"
    assert restore(looser, w).cases[0].expected[0].kind == "text_equals"
    renamed = plan.model_copy(deep=True)
    renamed.cases[0].expected[0].id = "TC-01.x9"  # same check, new id: not a weakening
    assert plan_weakenings(plan, renamed) == []
    gone = plan.model_copy(update={"cases": []})
    [case] = plan_weakenings(plan, gone)
    assert case.change == "case_removed"
    assert restore(gone, case).cases[0].id == "TC-01"

    before = "def test_a(page):\n    expect(x).to_be_visible()\n    assert y == 1\n"
    skipped = "import pytest\n\n@pytest.mark.skip\ndef test_a(page):\n" + before.split(":\n", 1)[1]
    assert [w.change for w in code_weakenings("tests/t.py", before, skipped)] == ["skipped"]
    fewer = "def test_a(page):\n    assert y == 1\n"
    assert [w.change for w in code_weakenings("tests/t.py", before, fewer)] == ["assertion_removed"]
    assert [w.change for w in code_weakenings("tests/t.py", before, "")] == ["test_removed"]
    assert code_weakenings("tests/t.py", before, before + "\n") == []

    details = (
        "page = <Page>\n>       expect(add_page.x).to_have_text('a')  # TC-01.x1 [requirement]\n"
        "E   AssertionError\n    expect(add_page.y).to_be_visible()  # TC-01.x2 [observation]\n"
    )
    assert failed_expectations(details) == ["TC-01.x1"]

    revision = json.loads(
        _offline_revision(
            json.loads(plan.model_dump_json()),
            "TC-01.x1 is wrong",
            {"run_results": [{"failed_expectations": []}]},
        )
    )
    assert revision["cases"] == plan.model_dump(mode="json")["cases"]  # nothing left: unchanged
    assert "removed failing check(s) TC-01.x1" in revision["notes"]
