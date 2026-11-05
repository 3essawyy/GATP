"""TC-208: rescan, snapshot diff and change flags (T-016)."""

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from gatp.maintainer.match import CLEAR, El, match_page, score

from .test_api_core import make_project
from .test_api_gates import approve
from .test_api_plan import LOGIN, fake  # noqa: F401 - fixtures
from .test_codegen import plan_approved


def _el(key: str, locator: str, **fp: Any) -> El:
    base = {"tag": "button", "role": "button", "type": "submit", "form": "f1", "index_in_form": 2}
    return El(key, True, {**base, **fp}, (locator,), locator)


SIGN_IN = _el(
    "e3",
    'page.get_by_role("button", name="Sign in")',
    name="Sign in",
    test_id="login-submit",
    center=[100, 200],
)
SAVE = _el(
    "e6",
    'page.get_by_role("button", name="Save")',
    name="Save",
    test_id="save-book",
    center=[80, 400],
)
USER = _el(
    "e1",
    'page.get_by_label("Username")',
    tag="input",
    role="textbox",
    type="text",
    name="Username",
    index_in_form=0,
)


def test_scoring_units() -> None:
    """Synthetic fingerprints: unchanged, clear rename, split -> ambiguous, missing."""
    log_in = _el(
        "e3",
        'page.get_by_role("button", name="Log in")',
        name="Log in",
        test_id="login-button",
        center=[100, 200],
    )
    changes, appeared = match_page([USER, SIGN_IN], [USER, log_in])
    assert changes["e1"].status == "unchanged"
    clear = changes["e3"]
    assert clear.status == "clear_match"
    assert clear.new_key == "e3"
    assert clear.candidates[0].score >= CLEAR
    assert {b["field"] for b in clear.candidates[0].breakdown} >= {"role", "name", "test_id"}
    assert appeared == []

    draft = _el(
        "e6",
        'page.get_by_role("button", name="Save draft")',
        name="Save draft",
        test_id="save-draft",
        center=[80, 400],
    )
    publish = _el(
        "e7",
        'page.get_by_role("button", name="Publish")',
        name="Publish",
        test_id="publish-book",
        index_in_form=3,
        center=[180, 400],
    )
    split = match_page([SAVE], [draft, publish])[0]["e6"]
    assert split.status == "ambiguous"
    assert split.new_key is None
    assert "2 similar new elements" in split.reason
    assert [c.key for c in split.candidates] == ["e6", "e7"]

    link = El("e9", True, {"tag": "a", "role": "link", "name": "Help", "href": "/help"}, (), "")
    assert match_page([SAVE], [link])[0]["e6"].status == "missing"
    renamed_text = _el("e3", SIGN_IN.default, name="Sign in now")  # locator kept (same expression)
    kept = match_page([SIGN_IN], [renamed_text])[0]["e3"]
    assert kept.status == "unchanged"
    assert "Sign in now" in kept.text_change
    same, breakdown = score(SAVE.fingerprint, SAVE.fingerprint)
    assert same == 1.0
    assert all(b["similarity"] == 1.0 for b in breakdown)


@pytest.fixture
def built_on_v1(client: TestClient, site_switchable: Any, fake: Any) -> dict[str, Any]:  # noqa: F811
    """Project on the switchable site: index + add (with sign-in setup), scope, approved plan."""
    base = site_switchable.url
    pid = make_project(client, base)["id"]
    index = client.get(f"/api/projects/{pid}/pages").json()[0]
    add = client.post(f"/api/projects/{pid}/pages", json={"url": f"{base}/add.html"}).json()
    client.put(
        f"/api/pages/{add['id']}/setup",
        json={"steps": json.loads(json.dumps(LOGIN).replace("{base}", base))},
    )
    snaps = {
        p["id"]: client.post(f"/api/pages/{p['id']}/inspections", json={}).json()["snapshot"]
        for p in (add, index)
    }
    body = {
        "pages": [
            {"snapshot_id": snaps[add["id"]]["id"]},
            {"snapshot_id": snaps[index["id"]]["id"]},
        ],
        "goal": "Add a book",
        "actor": "Abdo",
    }
    scope = client.put(f"/api/projects/{pid}/scope", json=body).json()
    assert approve(client, pid, "G0", scope["version"]["id"]).status_code == 201
    plan_approved(client, pid)  # TC-01 uses Author, Save and the title error region
    return {
        "pid": pid,
        "server": site_switchable,
        "add": snaps[add["id"]],
        "index": snaps[index["id"]],
    }


def _by_page(rescan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["summary"]["page_url"].rsplit("/", 1)[-1]: c for c in rescan["change_sets"]}


def _steps(client: TestClient, pid: int) -> dict[str, dict[str, Any]]:
    return {s["step"]: s for s in client.get(f"/api/projects/{pid}/workflow").json()}


def test_rescan_without_changes(client: TestClient, built_on_v1: dict[str, Any]) -> None:
    pid = built_on_v1["pid"]
    assert _steps(client, pid)["maintain"]["status"] == "todo"
    rescan = client.post(f"/api/projects/{pid}/rescans")
    assert rescan.status_code == 201, rescan.text
    body = rescan.json()
    assert body["summary"]["referenced_changes"] == 0
    pages = _by_page(body)
    assert pages["add.html"]["summary"]["counts"]["unchanged"] >= 3  # Author, Save, title error
    assert (
        pages["add.html"]["new_snapshot_id"] != built_on_v1["add"]["id"]
    )  # new immutable snapshot
    assert _steps(client, pid)["maintain"]["status"] == "approved"


def test_rescan_v1_to_v2_flags_clear_and_ambiguous(
    client: TestClient, built_on_v1: dict[str, Any]
) -> None:
    """Fixture v1 -> v2: FXC-1 (sign-in renamed) clear match; FXC-2 (Save split) ambiguous."""
    pid = built_on_v1["pid"]
    built_on_v1["server"].switch("v2")
    body = client.post(f"/api/projects/{pid}/rescans").json()
    pages = _by_page(body)

    index = pages["index.html"]["summary"]
    [sign_in] = [e for e in index["elements"] if e["referenced"] and e["status"] != "unchanged"]
    assert sign_in["status"] == "clear_match"
    assert sign_in["old_label"] == 'button "Sign in"'
    assert sign_in["new_label"] == 'button "Log in"'
    assert any("setup of" in u and "add.html step 4" in u for u in sign_in["used_by"])
    assert sign_in["candidates"][0]["breakdown"]  # evidence: per-field similarity

    # add.html: its sign-in setup step broke on that element, so the page was inspected
    # read-only with the proposed locator (nothing stored as a repair).
    add_row = next(p for p in body["summary"]["pages"] if p["page_url"].endswith("add.html"))
    assert add_row["error"] == ""
    assert add_row["trial_setup"]["step"] == 4
    assert 'name="Log in"' in add_row["trial_setup"]["proposed_locator"]
    add = pages["add.html"]["summary"]
    save = next(e for e in add["elements"] if e["old_label"] == 'button "Save"')
    assert save["status"] == "ambiguous"
    assert save["referenced"]
    assert save["used_by"] == ["TC-01"]
    assert {c["label"] for c in save["candidates"][:2]} == {
        'button "Save draft"',
        'button "Publish"',
    }
    assert add["html_changed"] is True  # FXC-3 footer text also changed (low impact)
    assert body["summary"]["referenced_changes"] == 2

    maintain = _steps(client, pid)["maintain"]
    assert maintain["status"] == "needs_approval"
    assert "2 used element(s) changed" in maintain["detail"]
    pages_now = client.get(f"/api/projects/{pid}/pages").json()
    setup = next(p for p in pages_now if p["url"].endswith("add.html"))["setup"]
    assert setup[3]["locator"]["value"] == "login-submit"  # stored setup untouched (needs G4)
    latest = client.get(f"/api/projects/{pid}/rescans/latest").json()
    assert latest["id"] == body["id"]
