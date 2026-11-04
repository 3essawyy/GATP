"""TC-203 / TC-204: code from the approved plan; validation (static, recount, collect); G2."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from gatp.codegen.validate import validate

from .test_api_gates import approve
from .test_api_plan import fake, scoped  # noqa: F401 - fixtures

ALLOWED = {'page.get_by_role("button", name="Save", exact=True)'}


def plan_approved(client: TestClient, pid: int) -> dict[str, Any]:
    plan = client.post(f"/api/projects/{pid}/plan/propose", json={}).json()
    for c in plan["open_clarifications"]:
        answer = "Confirm" if c["kind"] == "assumption" else "ok"
        client.post(f"/api/clarifications/{c['id']}/answer", json={"answer": answer, "actor": "A"})
    current: dict[str, Any] = client.get(f"/api/projects/{pid}/plan").json()
    assert approve(client, pid, "G1", current["version"]["id"]).status_code == 201
    return current


@pytest.mark.usefixtures("fake")
def test_generation_requires_g1(client: TestClient, scoped: dict[str, Any]) -> None:  # noqa: F811
    pid = scoped["pid"]
    assert client.post(f"/api/projects/{pid}/code/generate").status_code == 409
    client.post(f"/api/projects/{pid}/plan/propose", json={})
    assert client.post(f"/api/projects/{pid}/code/generate").status_code == 409  # not approved


@pytest.mark.usefixtures("fake")
def test_generate_validate_approve_and_edit(client: TestClient, scoped: dict[str, Any]) -> None:  # noqa: F811
    pid = scoped["pid"]
    plan = plan_approved(client, pid)
    code = client.post(f"/api/projects/{pid}/code/generate")
    assert code.status_code == 201, code.text
    files = {f["path"]: f for f in code.json()["files"]}
    assert set(files) == {
        "conftest.py",
        "pages/__init__.py",
        "pages/add_page.py",
        "tests/test_plan.py",
    }
    page_obj = files["pages/add_page.py"]["version"]["content"]
    tests = files["tests/test_plan.py"]["version"]["content"]
    assert f"test plan v{plan['version']['number']}" in page_obj  # linked to the plan version
    assert 'page.get_by_role("button", name="Save", exact=True)' in page_obj
    assert 'page.locator("#title-error")' in page_obj
    assert "def test_tc_01_title_is_required(page: Page, base_url: str)" in tests
    assert "expect(add_page.title_error_alert).to_have_text('Title is required.')" in tests
    assert "TC-01.x1: text_equals [requirement]" in tests
    assert files["tests/test_plan.py"]["version"]["author"] == "generator"

    blocked = client.post(f"/api/projects/{pid}/code/approve", json={"actor": "Abdo"})
    assert blocked.status_code == 409  # G2 needs a passing validation report
    validated = client.post(f"/api/projects/{pid}/code/validate").json()
    report = validated["report"]
    assert report["ok"] is True, report["report"]["collect"]["output"]
    assert report["report"]["static"]["findings"] == []
    assert all(i["count"] == 1 for i in report["report"]["recount"]["items"])
    assert report["report"]["collect"]["tests"] == [
        "tests/test_plan.py::test_tc_01_title_is_required[chromium]"  # per-browser parameter
    ]
    assert (
        client.post(f"/api/projects/{pid}/code/approve", json={"actor": "Abdo"}).status_code == 201
    )
    assert client.get(f"/api/projects/{pid}/code").json()["approved"] is True
    steps = {s["step"]: s["status"] for s in client.get(f"/api/projects/{pid}/workflow").json()}
    assert steps["code"] == "approved"

    # A reviewer edit is a new version: approval and the report no longer cover it (TC-204).
    tid = files["tests/test_plan.py"]["artifact_id"]
    edited = tests.replace("'Title is required.'", "'Title is required!'")
    client.post(
        f"/api/artifacts/{tid}/versions",
        json={"content": edited, "reason": "typo", "actor": "Abdo"},
    )
    after = client.get(f"/api/projects/{pid}/code").json()
    assert after["approved"] is False
    assert after["report"] is None  # stale report is not shown for new versions
    assert (
        client.post(f"/api/projects/{pid}/code/approve", json={"actor": "Abdo"}).status_code == 409
    )


@pytest.mark.usefixtures("fake")
def test_injected_invented_locator_is_caught(client: TestClient, scoped: dict[str, Any]) -> None:  # noqa: F811
    pid = scoped["pid"]
    plan_approved(client, pid)
    files = {
        f["path"]: f for f in client.post(f"/api/projects/{pid}/code/generate").json()["files"]
    }
    po = files["pages/add_page.py"]
    injected = po["version"]["content"].replace(
        'page.locator("#title-error")', 'page.locator("#made-up-error")'
    )
    client.post(
        f"/api/artifacts/{po['artifact_id']}/versions",
        json={"content": injected, "reason": "inject", "actor": "test"},
    )
    report = client.post(f"/api/projects/{pid}/code/validate").json()["report"]
    assert report["ok"] is False
    findings = report["report"]["static"]["findings"]
    assert [(f["check"], f["file"]) for f in findings] == [("locator", "pages/add_page.py")]
    assert "#made-up-error" in findings[0]["message"]
    assert report["report"]["collect"]["error"] == "skipped: static checks failed"
    assert client.post(f"/api/projects/{pid}/code/approve", json={"actor": "A"}).status_code == 409


def test_static_checks_unit() -> None:
    files = {
        "pages/a_page.py": "class A:\n    def __init__(self, page):\n"
        '        self.save = page.get_by_role("button", name="Save", exact=True)\n',
        "tests/test_x.py": "import subprocess\nfrom playwright.sync_api import Page\n\n"
        "def test_x(page: Page) -> None:\n"
        '    page.get_by_text("Hi").click()\n'
        '    subprocess.run(["id"])\n'
        "    eval('1')\n",
        "tests/test_bad.py": "def broken(:\n",
    }
    report = validate(files, ALLOWED)
    got = sorted((f.file, f.check) for f in report.findings)
    assert got == [
        ("tests/test_bad.py", "syntax"),
        ("tests/test_x.py", "safety"),  # import subprocess
        ("tests/test_x.py", "safety"),  # eval
        ("tests/test_x.py", "structure"),  # locator built in a test
    ]
    assert report.locators == [
        'page.get_by_role("button", name="Save", exact=True)'
    ] or report.locators == ["page.get_by_role('button', name='Save', exact=True)"]


@pytest.mark.usefixtures("fake")
def test_generated_tests_really_pass_on_fixture_v1(
    client: TestClient,
    scoped: dict[str, Any],  # noqa: F811
    site_v1: str,
    tmp_path: Any,
) -> None:
    """Not just collectable: the generated test runs in a browser and passes on v1."""
    import os
    import subprocess
    import sys

    pid = scoped["pid"]
    plan_approved(client, pid)
    files = client.post(f"/api/projects/{pid}/code/generate").json()["files"]
    for f in files:
        target = tmp_path / f["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f["version"]["content"], encoding="utf-8")
    env = {**os.environ, "GATP_BASE_URL": site_v1, "GATP_HEADLESS": "1"}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout[-3000:]
    assert "1 passed" in result.stdout
