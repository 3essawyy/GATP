"""TC-106: executor runs jobs in a browser, aborts and logs requests outside the allowlist."""

import threading
from collections.abc import Iterator
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from gatp.config import get_settings
from gatp.inspector.locators import LocatorSpec
from gatp.runner.browser import BrowserOptions
from gatp.runner.executor import JobExecutor
from gatp.runner.jobs import InspectJob, RecountJob


@pytest.fixture
def executor(tmp_path: Path) -> JobExecutor:
    opts = BrowserOptions(headless=True, executable_path=get_settings().chromium_executable)
    return JobExecutor(opts, tmp_path / "sandbox", tmp_path / "artifacts")


def _serve(directory: Path) -> Iterator[str]:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(directory))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


@pytest.fixture
def linking_out(tmp_path: Path) -> Iterator[tuple[str, str]]:
    """A page on origin A that loads an image and a script from origin B."""
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    (other_dir / "pixel.gif").write_bytes(b"GIF89a")
    (other_dir / "track.js").write_text("document.title = 'tracked';")
    other = _serve(other_dir)
    other_url = next(other)
    page_dir = tmp_path / "page"
    page_dir.mkdir()
    (page_dir / "index.html").write_text(
        f"<html><head><title>Local</title><script src='{other_url}/track.js'></script></head>"
        f"<body><img src='{other_url}/pixel.gif'><a href='{other_url}/'>out</a></body></html>"
    )
    local = _serve(page_dir)
    yield next(local), other_url
    for gen in (local, other):
        next(gen, None)


def test_inspect_fixture_site(executor: JobExecutor, site_v1: str, tmp_path: Path) -> None:
    result = executor.run(InspectJob(url=f"{site_v1}/index.html", allowlist=[site_v1]))
    assert result.status == "ok", result.error
    assert result.data["title"] == "BookShelf · Sign in"
    assert result.blocked_requests == []
    shot = tmp_path / "artifacts" / result.files["screenshot"]
    assert shot.read_bytes().startswith(b"\x89PNG")
    assert not any((tmp_path / "sandbox").iterdir())  # sandbox cleaned up


def test_requests_outside_allowlist_are_blocked_and_logged(
    executor: JobExecutor, linking_out: tuple[str, str]
) -> None:
    local, other = linking_out
    result = executor.run(InspectJob(url=f"{local}/index.html", allowlist=[local]))
    assert result.status == "ok", result.error
    assert result.data["title"] == "Local"  # the external script never ran
    blocked = {(b.url, b.resource_type) for b in result.blocked_requests}
    assert (f"{other}/track.js", "script") in blocked
    assert (f"{other}/pixel.gif", "image") in blocked


def test_recount_reports_match_counts(executor: JobExecutor, site_v1: str) -> None:
    specs = [
        LocatorSpec(strategy="test_id", value="login-submit"),
        LocatorSpec(strategy="role", value="button", name="Sign in"),
        LocatorSpec(strategy="role", value="textbox"),
        LocatorSpec(strategy="css", value="#does-not-exist"),
    ]
    result = executor.run(
        RecountJob(url=f"{site_v1}/index.html", allowlist=[site_v1], locators=specs)
    )
    assert result.status == "ok", result.error
    assert result.data["counts"] == [1, 1, 2, 0]


def test_navigation_failure_is_reported(executor: JobExecutor) -> None:
    result = executor.run(
        InspectJob(url="http://127.0.0.1:9/nothing", allowlist=["http://127.0.0.1:9"], timeout_s=5)
    )
    assert result.status == "failed"
    assert result.error
