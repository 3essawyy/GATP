"""TC-107 (automated part) / TC-108: extraction, ranked + verified locators, flags, scope."""

from pathlib import Path
from typing import Any

import pytest

from gatp.api.inspections import to_snapshot_in
from gatp.config import get_settings
from gatp.inspector.inspect import candidate_specs, source_lines
from gatp.inspector.locators import STRATEGY_RANK, LocatorSpec
from gatp.inspector.models import InspectedElement, InspectionResult, InspectionScope
from gatp.runner.browser import BrowserOptions
from gatp.runner.executor import JobExecutor
from gatp.runner.jobs import InspectJob, SetupStep
from gatp.store.db import Database
from gatp.store.projects import ProjectRepository
from gatp.store.snapshots import SnapshotRepository


@pytest.fixture(scope="module")
def executor(tmp_path_factory: pytest.TempPathFactory) -> JobExecutor:
    base = tmp_path_factory.mktemp("insp")
    opts = BrowserOptions(headless=True, executable_path=get_settings().chromium_executable)
    return JobExecutor(opts, base / "sandbox", base / "artifacts")


def login_steps(base: str) -> list[SetupStep]:
    def loc(strategy: str, value: str) -> LocatorSpec:
        return LocatorSpec.model_validate({"strategy": strategy, "value": value})

    return [
        SetupStep(action="goto", url=f"{base}/index.html"),
        SetupStep(action="fill", locator=loc("label", "Username"), value="tester"),
        SetupStep(action="fill", locator=loc("label", "Password"), value="secret123"),
        SetupStep(action="click", locator=loc("test_id", "login-submit")),
    ]


def inspect(executor: JobExecutor, base: str, page: str, **kw: Any) -> InspectionResult:
    result = executor.run(InspectJob(url=f"{base}/{page}", allowlist=[base], **kw))
    assert result.status == "ok", result.error
    assert set(result.files) == {"screenshot", "html"}
    return InspectionResult.model_validate(result.data)


def interactive(result: InspectionResult) -> list[InspectedElement]:
    return [e for e in result.elements if e.interactive]


def by_name(result: InspectionResult) -> dict[str, InspectedElement]:
    return {e.name or e.dom_path: e for e in interactive(result)}


def best(e: InspectedElement) -> str:
    assert e.default_locator is not None, e.flags
    return e.locators[e.default_locator].expression


def test_login_page_elements_and_best_locators(executor: JobExecutor, site_v1: str) -> None:
    result = inspect(executor, site_v1, "index.html")
    assert result.title == "BookShelf · Sign in"
    assert [(e.key, e.tag, e.role, e.name) for e in interactive(result)] == [
        ("e1", "input", "textbox", "Username"),
        ("e2", "input", "", "Password"),  # password inputs have no ARIA role
        ("e3", "button", "button", "Sign in"),
    ]
    els = by_name(result)
    assert best(els["Username"]) == 'page.get_by_role("textbox", name="Username", exact=True)'
    assert best(els["Password"]) == 'page.get_by_label("Password", exact=True)'
    assert best(els["Sign in"]) == 'page.get_by_role("button", name="Sign in", exact=True)'
    assert [e.source_line for e in interactive(result)] == [16, 20, 23]
    for e in interactive(result):
        ranks = [c.rank for c in e.locators]
        assert ranks == sorted(ranks), "candidates must be in ADR-006 priority order"
        assert e.flags == []
        assert e.fingerprint["form"] == "login-form"


def test_books_page_needs_setup_and_flags_poor_labels(executor: JobExecutor, site_v1: str) -> None:
    result = inspect(executor, site_v1, "books.html", setup=login_steps(site_v1))
    assert result.final_url.endswith("/books.html")
    names = [(e.tag, e.name) for e in interactive(result)]
    assert names == [("button", "⎋"), ("input", "Search books"), ("select", ""), ("a", "Add book")]
    logout, search, genre, add = interactive(result)
    assert "weak_accessible_name" in logout.flags
    assert {"no_accessible_name", "no_visible_label"} <= set(genre.flags)
    assert best(genre) == 'page.locator("#genre-filter")'
    assert best(search).startswith('page.get_by_role("searchbox"')
    assert any(c.spec.strategy == "test_id" and c.usable for c in add.locators)


def test_signed_out_redirect_is_reported(executor: JobExecutor, site_v1: str) -> None:
    result = inspect(executor, site_v1, "books.html")
    assert result.url.endswith("/books.html")
    assert result.final_url.endswith("/index.html")
    assert [e.name for e in interactive(result)] == ["Username", "Password", "Sign in"]


def test_add_page_and_scope(executor: JobExecutor, site_v1: str) -> None:
    full = inspect(executor, site_v1, "add.html", setup=login_steps(site_v1))
    assert [e.name for e in interactive(full)] == [
        "Back to books",
        "Title",
        "Author",
        "Year published",
        "Genre",
        "Save",
        "Cancel",
    ]
    year = by_name(full)["Year published"]
    assert "no_visible_label" in year.flags
    scoped = inspect(
        executor,
        site_v1,
        "add.html",
        setup=login_steps(site_v1),
        scope=InspectionScope(include=["#book-form"], exclude=["a"]),
    )
    expected = ["Title", "Author", "Year published", "Genre", "Save"]
    assert [e.name for e in interactive(scoped)] == expected


@pytest.fixture
def duplicates(tmp_path: Path) -> Any:
    import threading
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    (tmp_path / "dup.html").write_text(
        "<html><head><title>Dup</title></head><body>"
        "<ul><li>Alpha <button>Delete</button></li><li>Beta <button>Delete</button></li></ul>"
        "<label>Note <input name='note'></label><label>Note <input name='note2'></label>"
        "</body></html>"
    )
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def test_non_unique_locators_unusable_and_flagged(executor: JobExecutor, duplicates: str) -> None:
    result = inspect(executor, duplicates, "dup.html")
    delete1, delete2, note1, note2 = result.elements
    for e in (delete1, delete2):
        role = e.locators[0]
        assert role.spec.strategy == "role"
        assert role.count == 2
        assert not role.usable
        assert e.default_locator is None
        assert "no_unique_locator" in e.flags
        positional = e.locators[-1]
        assert positional.positional
        assert positional.usable  # evidence only; never chosen as default
    for e in (note1, note2):
        assert e.locators[0].count == 2  # role textbox "Note" matches both
        assert best(e) in (
            'page.locator("input[name=\\"note\\"]")',
            'page.locator("input[name=\\"note2\\"]")',
        )


def test_setup_urls_must_be_allowlisted() -> None:
    with pytest.raises(ValueError, match="setup url"):
        InspectJob(
            url="http://a.test/x",
            allowlist=["http://a.test"],
            setup=[SetupStep(action="goto", url="http://evil.test/")],
        )
    with pytest.raises(ValueError, match="needs a locator"):
        SetupStep(action="click")


def test_candidate_specs_and_source_lines_unit() -> None:
    raw = {
        "tag": "button",
        "role": "button",
        "name": "Save",
        "label": "",
        "text": "Save",
        "dom_path": "form#f > button",
        "attributes": {"data-testid": "save", "id": "save-btn"},
    }
    strategies = [s.strategy for s in candidate_specs(raw)]
    assert strategies == ["role", "test_id", "text", "css", "css"]
    assert [STRATEGY_RANK[s] for s in strategies] == sorted(STRATEGY_RANK[s] for s in strategies)
    html = '<p>\n<input id="a" name="a" />\n<button id="b">'
    tags = ['<input id="a" name="a">', '<button id="b">', "<em>"]
    assert source_lines(html, tags) == [2, 3, None]


def test_snapshot_persists_full_evidence(executor: JobExecutor, site_v1: str, db: Database) -> None:
    result = inspect(executor, site_v1, "index.html")
    projects = ProjectRepository(db)
    project = projects.create("BookShelf", site_v1)
    page = projects.add_page(project.id, f"{site_v1}/index.html")
    snap = SnapshotRepository(db).save(
        to_snapshot_in(
            page.id, result, {"screenshot": "jobs/x/page.png", "html": "jobs/x/page.html"}
        )
    )
    sign_in = snap.elements[2]
    assert sign_in.name == "Sign in"
    assert sign_in.details["default_locator"] == 0
    assert sign_in.locators[0].unique
    assert sign_in.locators[0].spec["strategy"] == "role"
    assert snap.screenshot_path == "jobs/x/page.png"
    assert snap.html_sha256 == result.html_sha256


def test_observable_regions_for_expected_results(executor: JobExecutor, site_v1: str) -> None:
    """Alerts, status, headings and tables are recorded (o-keys) so expectations can check them."""
    result = inspect(executor, site_v1, "add.html", setup=login_steps(site_v1))
    obs = [e for e in result.elements if not e.interactive]
    assert [(e.key, e.tag, e.role) for e in obs] == [
        ("o1", "h1", "heading"),
        ("o2", "span", "alert"),
        ("o3", "span", "alert"),
        ("o4", "span", "alert"),
        ("o5", "span", "alert"),
    ]
    title_error = obs[1]
    assert title_error.attributes["id"] == "title-error"
    assert title_error.locators[title_error.default_locator or 0].expression == (
        'page.locator("#title-error")'
    )
    assert "no_accessible_name" not in title_error.flags  # names are not expected on regions
