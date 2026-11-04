"""Shared pytest fixtures."""

from __future__ import annotations

import importlib.util
import sys
import threading
from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import Browser, Page, sync_playwright

from gatp.api.app import create_app
from gatp.api.services import Services, build_services
from gatp.config import Settings, get_settings
from gatp.runner.browser import BrowserOptions
from gatp.runner.client import RunnerUnavailableError
from gatp.runner.executor import JobExecutor
from gatp.runner.jobs import JobResult
from gatp.store.db import Database

REPO_ROOT = Path(__file__).resolve().parents[2]


class InProcessRunner:
    """Runner stand-in for API tests: same job models, real headless executor, no socket."""

    def __init__(self, executor: JobExecutor | None) -> None:
        self.executor = executor
        self.jobs: list[Any] = []

    def health(self) -> dict[str, Any]:
        if self.executor is None:
            raise RunnerUnavailableError("runner not reachable (test)")
        return {"status": "ok", "headless": "true"}

    def submit(self, job: Any) -> JobResult:
        self.jobs.append(job)
        if self.executor is None:
            raise RunnerUnavailableError("runner not reachable; start it with `uv run poe runner`")
        return self.executor.run(job)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path / "data",
        artifacts_dir=tmp_path / "artifacts",
        runner_sandbox_dir=tmp_path / "sandbox",
        runner_headless=True,
        llm_primary="fake",
        llm_fallback="",
    )


@pytest.fixture
def runner(settings: Settings) -> InProcessRunner:
    options = BrowserOptions(headless=True, executable_path=get_settings().chromium_executable)
    return InProcessRunner(
        JobExecutor(options, settings.runner_sandbox_dir, settings.artifacts_dir)
    )


@pytest.fixture
def services(settings: Settings, runner: InProcessRunner) -> Services:
    svc = build_services(settings)
    svc.runner = runner  # type: ignore[assignment]
    return svc


@pytest.fixture
def client(services: Services) -> Iterator[TestClient]:
    """A TestClient for a fresh app with an isolated database and an in-process runner."""
    with TestClient(create_app(services=services)) as c:
        yield c


def _load_fixture_server() -> ModuleType:
    """Import fixtures/serve.py (it lives outside the gatp package on purpose)."""
    path = REPO_ROOT / "fixtures" / "serve.py"
    spec = importlib.util.spec_from_file_location("fixture_serve", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fixture_serve"] = module
    spec.loader.exec_module(module)
    return module


fixture_serve = _load_fixture_server()


def _serve(version: str) -> Iterator[str]:
    server: ThreadingHTTPServer = fixture_serve.make_server(version, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture(scope="session")
def site_v1() -> Iterator[str]:
    """Base URL of the BookShelf v1 fixture site on a free port."""
    yield from _serve("v1")


@pytest.fixture(scope="session")
def site_v2() -> Iterator[str]:
    """Base URL of the BookShelf v2 fixture site on a free port."""
    yield from _serve("v2")


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """One headless Chromium for the whole test session."""
    executable = get_settings().chromium_executable or None
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, executable_path=executable)
        yield b
        b.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    """A fresh browser context + page per test (isolated localStorage)."""
    context = browser.new_context()
    p = context.new_page()
    yield p
    context.close()


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """A fresh, migrated SQLite database in a temp folder."""
    database = Database(f"sqlite:///{tmp_path / 'data' / 'gatp.sqlite'}")
    database.migrate()
    return database
