"""Shared pytest fixtures."""

from __future__ import annotations

import importlib.util
import sys
import threading
from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import Browser, Page, sync_playwright

from gatp.api.app import create_app
from gatp.config import get_settings
from gatp.store.db import Database

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient for a fresh app instance."""
    with TestClient(create_app()) as c:
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
